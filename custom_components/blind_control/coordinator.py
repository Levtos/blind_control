"""Running Home Assistant observation coordinator for Shadow mode.

The coordinator reads only owner-selected state entities, evaluates the pure
engine, and publishes an in-memory/read-only projection.  It contains no
service call, actuator callback, or cover command.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    from homeassistant.core import callback
except ImportError:  # pragma: no cover - enables the HA-independent contract tests

    def callback[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        """Fallback marker when Home Assistant is intentionally absent in tests."""

        return func


from .config import (
    INPUT_BINDING_KEYS,
    LEGACY_BINDING_KEYS,
    BindingFreshness,
    BlindControlConfig,
)
from .contracts import (
    BlindControlInputs,
    InputObservation,
    InputQuality,
    LegacyEvidence,
)
from .shadow import ShadowRuntime, ShadowSnapshot
from .ux_contract import build_ux_snapshot

_BOOLEAN_KEYS = frozenset(
    {
        "away",
        "private_time",
        "privacy",
        "opening_safe_for_blind",
        "cover_available",
        "cover_ready",
        "weather_alert",
        "air_movement",
    }
)
_NUMERIC_KEYS = frozenset(
    {
        "cover_position",
        "outdoor_lux",
        "lux_trend",
        "sun_elevation",
        "sun_azimuth",
        "expected_direct_radiation",
        "expected_diffuse_radiation",
        "cloud_cover",
        "indoor_temperature",
        "outdoor_temperature",
        "indoor_temperature_trend",
        "outdoor_temperature_trend",
        "precipitation_trend",
        "wind_trend",
        "pressure_trend",
        "effective_target",
    }
)
_STATE_UNAVAILABLE = frozenset({"unknown", "unavailable"})


def build_inputs_from_states(
    states: Mapping[str, object],
    config: BlindControlConfig,
    *,
    now: datetime | None = None,
) -> BlindControlInputs:
    """Build the complete input contract from configured HA state objects."""

    now = now or datetime.now(UTC)
    configured = dict(config.input_bindings)
    values = {
        key: _observation_for_entity(
            key,
            configured.get(key),
            states.get(configured[key]) if key in configured else None,
            config.binding_policy(key),
            now,
        )
        for key in INPUT_BINDING_KEYS
    }
    return BlindControlInputs(**values)


def build_legacy_evidence_from_states(
    states: Mapping[str, object],
    config: BlindControlConfig,
    *,
    now: datetime | None = None,
) -> LegacyEvidence:
    """Read all configured old-policy fields, including explicit missing fields."""

    if not config.legacy_bindings:
        return LegacyEvidence.empty()
    now = now or datetime.now(UTC)
    configured = dict(config.legacy_bindings)
    observations: list[tuple[str, InputObservation[object]]] = []
    for key in LEGACY_BINDING_KEYS:
        entity_id = configured.get(key)
        observations.append(
            (
                key,
                _observation_for_entity(
                    key,
                    entity_id,
                    states.get(entity_id) if entity_id else None,
                    config.binding_policy(key, legacy=True),
                    now,
                ),
            )
        )
    return LegacyEvidence(observations=tuple(observations), configured=True)


class ShadowCoordinator:
    """Re-evaluate Shadow state on configured entity changes and a timer."""

    def __init__(
        self,
        hass: object,
        entry: object,
        config: BlindControlConfig,
        shadow: ShadowRuntime,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.config = config
        self.shadow = shadow
        self.snapshot: ShadowSnapshot | None = None
        self.ux_snapshot: dict[str, object] | None = None
        self._unsubscribers: list[object] = []
        self._snapshot_listeners: list[Callable[[], None]] = []
        self._refresh_task: asyncio.Task[object] | None = None
        self._restart_baseline_established = False

    @property
    def entity_ids(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                entity_id
                for _, entity_id in (*self.config.input_bindings, *self.config.legacy_bindings)
            )
        )

    async def async_start(self) -> ShadowSnapshot:
        """Evaluate immediately and install only state/time listeners."""

        snapshot = await self.async_refresh()
        try:
            from homeassistant.helpers.event import (
                async_track_state_change_event,
                async_track_time_interval,
            )
        except ImportError:
            return snapshot

        if self.entity_ids:
            self._unsubscribers.append(
                async_track_state_change_event(self.hass, self.entity_ids, self._state_changed)
            )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass,
                self._time_changed,
                timedelta(seconds=self.config.freshness_timer_seconds()),
            )
        )
        return snapshot

    def stop(self) -> None:
        """Remove observation listeners without invoking any HA service."""

        for unsubscribe in self._unsubscribers:
            if callable(unsubscribe):
                unsubscribe()
        self._unsubscribers.clear()
        self._snapshot_listeners.clear()
        if self._refresh_task is not None and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._refresh_task = None

    async def async_refresh(self) -> ShadowSnapshot:
        now = datetime.now(UTC)
        states = {
            entity_id: self.hass.states.get(entity_id)
            for entity_id in self.entity_ids
            if getattr(self.hass, "states", None) is not None
        }
        inputs = build_inputs_from_states(states, self.config, now=now)
        legacy = build_legacy_evidence_from_states(states, self.config, now=now)
        position = _number_value(inputs.cover_position)
        if not self._restart_baseline_established:
            self.shadow.on_restart(position)
            self._restart_baseline_established = True
        elif inputs.cover_position.usable:
            self.shadow.observe_cover_position(
                position,
                source=inputs.cover_position.source,
                now=time.monotonic(),
                observed_at=now,
            )
        snapshot = self.shadow.evaluate(
            inputs,
            evaluated_at=now,
            now=time.monotonic(),
            legacy_snapshot=legacy,
        )
        self.snapshot = snapshot
        self.ux_snapshot = build_ux_snapshot(snapshot, self.config)
        runtime_data = getattr(self.entry, "runtime_data", None)
        if runtime_data is not None:
            runtime_data.snapshot = snapshot
            runtime_data.ux_snapshot = self.ux_snapshot
        self._notify_snapshot_listeners()
        return snapshot

    @callback
    def async_add_snapshot_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Subscribe a read-only platform projection to future Shadow snapshots."""

        self._snapshot_listeners.append(listener)

        @callback
        def _remove_listener() -> None:
            if listener in self._snapshot_listeners:
                self._snapshot_listeners.remove(listener)

        return _remove_listener

    @callback
    def _notify_snapshot_listeners(self) -> None:
        """Notify only in-memory read-only consumers after an evaluated snapshot."""

        for listener in tuple(self._snapshot_listeners):
            listener()

    @callback
    def _state_changed(self, *_args: object) -> None:
        """Receive state events in HA's event loop and request a refresh safely."""

        self._schedule_refresh()

    @callback
    def _time_changed(self, *_args: object) -> None:
        """Receive timer events in HA's event loop and request a refresh safely."""

        self._schedule_refresh()

    @callback
    def _schedule_refresh(self) -> None:
        """Hop through Home Assistant's thread-safe scheduler before task creation."""

        add_job = getattr(self.hass, "add_job", None)
        if callable(add_job):
            add_job(self._schedule_refresh_in_event_loop)
            return

        loop = getattr(self.hass, "loop", None)
        if loop is not None:
            loop.call_soon_threadsafe(self._schedule_refresh_in_event_loop)
            return

        # This fallback is only for the minimal local fakes used by pure tests.
        asyncio.get_running_loop().call_soon(self._schedule_refresh_in_event_loop)

    @callback
    def _schedule_refresh_in_event_loop(self) -> None:
        """Create the coroutine only after the scheduler reached HA's event loop."""

        if self._refresh_task is not None and not self._refresh_task.done():
            return
        create_task = getattr(self.hass, "async_create_task", None)
        if callable(create_task):
            self._refresh_task = create_task(self.async_refresh())
        else:
            self._refresh_task = asyncio.create_task(self.async_refresh())


def _observation_for_entity(
    key: str,
    entity_id: str | None,
    state: object | None,
    freshness: BindingFreshness,
    now: datetime,
) -> InputObservation[Any]:
    if entity_id is None:
        return InputObservation.missing(reason="owner_binding_not_configured")
    if state is None:
        return InputObservation.missing(source=entity_id, reason="bound_entity_not_found")
    raw_state = getattr(state, "state", None)
    if raw_state is None:
        return InputObservation.missing(source=entity_id, reason="state_value_missing")
    if str(raw_state).lower() in _STATE_UNAVAILABLE:
        quality = (
            InputQuality.UNAVAILABLE
            if str(raw_state).lower() == "unavailable"
            else InputQuality.UNKNOWN
        )
        return InputObservation(
            source=entity_id,
            quality=quality,
            reason="bound_entity_state_not_usable",
            updated_at=_updated_at(key, state),
        )
    raw_value = _attribute_value(key, state, raw_state)
    try:
        value = _convert_value(key, raw_value)
    except (TypeError, ValueError):
        return InputObservation(
            source=entity_id,
            quality=InputQuality.DEGRADED,
            reason="bound_entity_value_parse_error",
            updated_at=_updated_at(key, state),
        )
    updated_at = _updated_at(key, state)
    quality, reason = _freshness(updated_at, now, freshness)
    return InputObservation(
        value=value,
        source=entity_id,
        quality=quality,
        reason=reason,
        updated_at=updated_at,
    )


def _attribute_value(key: str, state: object, raw_state: object) -> object:
    attributes = getattr(state, "attributes", {}) or {}
    attribute_key = {
        "sun_elevation": "elevation",
        "sun_azimuth": "azimuth",
        "cover_position": "current_position",
    }.get(key)
    if attribute_key and attribute_key in attributes:
        return attributes[attribute_key]
    return raw_state


def _convert_value(key: str, value: object) -> object:
    if key in _BOOLEAN_KEYS:
        normalized = str(value).lower()
        if normalized in {"on", "true", "yes", "1", "open", "home"}:
            return True
        if normalized in {"off", "false", "no", "0", "closed", "away"}:
            return False
        raise ValueError("boolean state is not canonical")
    if key in _NUMERIC_KEYS:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("numeric state is not finite")
        return result
    return str(value)


def _updated_at(key: str, state: object) -> datetime | None:
    if key == "cover_position":
        return _device_timestamp(state)
    return _ha_updated_at(state)


def _ha_updated_at(state: object) -> datetime | None:
    value = getattr(state, "last_updated", None) or getattr(state, "last_changed", None)
    return _as_utc_datetime(value)


def _device_timestamp(state: object) -> datetime | None:
    """Read source/device evidence, never HA state-change time, for cover position."""

    attributes = getattr(state, "attributes", {}) or {}
    for name in ("device_timestamp", "source_timestamp", "measurement_timestamp", "observed_at"):
        if name in attributes:
            timestamp = _as_utc_datetime(attributes[name])
            if timestamp is not None:
                return timestamp
    return None


def _as_utc_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _freshness(
    updated_at: datetime | None,
    now: datetime,
    policy: BindingFreshness,
) -> tuple[InputQuality, str]:
    if updated_at is None:
        if policy.require_timestamp:
            return InputQuality.STALE, "required_timestamp_missing"
        return InputQuality.FRESH, "stateful_contract_timestamp_not_required"
    if policy.max_age_seconds is None:
        return InputQuality.FRESH, "stateful_contract_not_age_limited"
    age = max(0.0, (now - updated_at).total_seconds())
    if age <= policy.max_age_seconds:
        return InputQuality.FRESH, "bound_entity_state_is_fresh"
    return InputQuality.STALE, "bound_entity_state_exceeded_freshness_window"


def _number_value(observation: InputObservation[object]) -> float | None:
    if not observation.usable:
        return None
    value = float(observation.value)
    return value if math.isfinite(value) else None
