"""Running Home Assistant observation and guarded apply coordinator.

The coordinator reads owner-selected state entities and evaluates the pure
engine. The isolated apply adapter remains unreachable in Shadow mode.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    from homeassistant.core import callback
except ImportError:  # pragma: no cover - enables the HA-independent contract tests

    def callback[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        """Fallback marker when Home Assistant is intentionally absent in tests."""

        return func


from .apply import CoverApplyExecutor
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
from .open_meteo import OPEN_METEO_PROVIDER
from .shadow import ShadowRuntime, ShadowSnapshot
from .ux_contract import build_ux_snapshot

_BOOLEAN_KEYS = frozenset(
    {
        "private_time",
        "privacy",
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
_CANONICAL_DAY_STATES = frozenset(
    {
        "early_night",
        "late_night",
        "early_morning",
        "forenoon",
        "midday",
        "afternoon",
        "late_afternoon",
        "evening",
        "late_evening",
    }
)


def build_inputs_from_states(
    states: Mapping[str, object],
    config: BlindControlConfig,
    *,
    now: datetime | None = None,
    provider_observations: Mapping[str, InputObservation[float]] | None = None,
) -> BlindControlInputs:
    """Build the complete input contract from configured HA state objects."""

    now = now or datetime.now(UTC)
    configured = dict(config.input_bindings)
    provider_observations = provider_observations or {}
    values = {}
    for key in INPUT_BINDING_KEYS:
        if key not in configured and key in provider_observations:
            values[key] = provider_observations[key]
            continue
        values[key] = _observation_for_entity(
            key,
            configured.get(key),
            states.get(configured[key]) if key in configured else None,
            config.binding_policy(key),
            now,
            opening_safety_polarity=config.opening_safety_polarity,
        )
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
        radiation_provider: object | None = None,
        apply_executor: CoverApplyExecutor | None = None,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.config = config
        self.shadow = shadow
        self.radiation_provider = radiation_provider
        self.apply_executor = apply_executor or CoverApplyExecutor(hass, config, shadow)
        self.snapshot: ShadowSnapshot | None = None
        self.ux_snapshot: dict[str, object] | None = None
        self._unsubscribers: list[object] = []
        self._snapshot_listeners: list[Callable[[], None]] = []
        self._refresh_task: asyncio.Task[object] | None = None
        self._refresh_requested = False
        self._restart_baseline_established = False
        self._previous_lux_sample: tuple[float, datetime] | None = None
        self._derived_lux_trend: InputObservation[float] | None = None

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
        if self.radiation_provider is not None:
            add_listener = getattr(self.radiation_provider, "async_add_listener", None)
            if callable(add_listener):
                self._unsubscribers.append(add_listener(self._provider_updated))
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
        self._refresh_requested = False

    async def async_refresh(self) -> ShadowSnapshot:
        now = datetime.now(UTC)
        states = {
            entity_id: self.hass.states.get(entity_id)
            for entity_id in self.entity_ids
            if getattr(self.hass, "states", None) is not None
        }
        inputs = self._with_derived_lux_trend(
            build_inputs_from_states(
                states,
                self.config,
                now=now,
                provider_observations=_radiation_provider_observations(
                    self.radiation_provider,
                    now=now,
                ),
            )
        )
        legacy = build_legacy_evidence_from_states(states, self.config, now=now)
        position = _number_value(inputs.cover_position)
        runtime_ready = self._restart_baseline_established
        if not runtime_ready:
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
            runtime_ready=runtime_ready,
        )
        snapshot = await self.apply_executor.async_apply(snapshot)
        self.snapshot = snapshot
        self.ux_snapshot = build_ux_snapshot(
            snapshot,
            self.config,
            provider_status=_radiation_provider_status(self.radiation_provider, now=now),
        )
        runtime_data = getattr(self.entry, "runtime_data", None)
        if runtime_data is not None:
            runtime_data.snapshot = snapshot
            runtime_data.ux_snapshot = self.ux_snapshot
        self._notify_snapshot_listeners()
        return snapshot

    def _with_derived_lux_trend(self, inputs: BlindControlInputs) -> BlindControlInputs:
        """Derive a local lux delta only when no trend owner is configured."""

        if "lux_trend" in dict(self.config.input_bindings):
            return inputs
        lux = inputs.outdoor_lux
        if not lux.usable or lux.updated_at is None:
            return replace(
                inputs,
                lux_trend=InputObservation.missing(
                    source=lux.source,
                    reason="derived_lux_trend_waiting_for_fresh_lux",
                ),
            )
        current = (float(lux.value), lux.updated_at)
        previous = self._previous_lux_sample
        if previous is None:
            self._previous_lux_sample = current
        elif current[1] > previous[1]:
            self._derived_lux_trend = InputObservation(
                value=current[0] - previous[0],
                source=lux.source,
                quality=InputQuality.FRESH,
                reason="derived_from_consecutive_fresh_lux_observations",
                updated_at=current[1],
            )
            self._previous_lux_sample = current
        if self._derived_lux_trend is None:
            return replace(
                inputs,
                lux_trend=InputObservation.missing(
                    source=lux.source,
                    reason="derived_lux_trend_waiting_for_previous_sample",
                ),
            )
        return replace(inputs, lux_trend=self._derived_lux_trend)

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
    def _provider_updated(self) -> None:
        """Re-evaluate Shadow after one read-only provider refresh."""

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
            self._refresh_requested = True
            return
        create_task = getattr(self.hass, "async_create_task", None)
        if callable(create_task):
            self._refresh_task = create_task(self.async_refresh())
        else:
            self._refresh_task = asyncio.create_task(self.async_refresh())
        self._refresh_task.add_done_callback(self._refresh_finished)

    @callback
    def _refresh_finished(self, _task: asyncio.Task[object]) -> None:
        """Run one coalesced follow-up when an event arrived during refresh."""

        if not self._refresh_requested:
            return
        self._refresh_requested = False
        self._schedule_refresh()


def _radiation_provider_status(provider: object | None, *, now: datetime) -> str:
    if provider is None:
        return "unconfigured"
    status = getattr(provider, "provider_status", None)
    return status(now=now) if callable(status) else "unavailable"


def _radiation_provider_observations(
    provider: object | None,
    *,
    now: datetime,
) -> dict[str, InputObservation[float]]:
    """Project provider data without exposing its private request URL."""

    status = _radiation_provider_status(provider, now=now)
    data = getattr(provider, "data", None) if provider is not None else None
    keys = {
        "expected_direct_radiation": "direct_normal_irradiance",
        "expected_diffuse_radiation": "diffuse_radiation",
    }
    if status == "unconfigured":
        return {
            key: InputObservation.missing(
                source=OPEN_METEO_PROVIDER,
                reason="internal_provider_not_configured",
            )
            for key in keys
        }
    if data is None:
        return {
            key: InputObservation(
                source=OPEN_METEO_PROVIDER,
                quality=InputQuality.UNAVAILABLE,
                reason="internal_provider_first_update_unavailable",
            )
            for key in keys
        }
    quality = InputQuality.STALE if status == "stale" else InputQuality.FRESH
    reason = {
        "ready": "internal_provider_fresh",
        "degraded": "internal_provider_last_success_within_freshness",
        "stale": "internal_provider_last_success_stale",
    }.get(status, "internal_provider_unavailable")
    return {
        key: InputObservation(
            value=float(getattr(data, attribute)),
            source=OPEN_METEO_PROVIDER,
            quality=quality,
            reason=reason,
            updated_at=getattr(data, "fetched_at", None),
        )
        for key, attribute in keys.items()
    }


def _observation_for_entity(
    key: str,
    entity_id: str | None,
    state: object | None,
    freshness: BindingFreshness,
    now: datetime,
    *,
    opening_safety_polarity: str = "unspecified",
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
    attributes = getattr(state, "attributes", {}) or {}
    if _true_bool(attributes.get("restored")):
        return InputObservation(
            source=entity_id,
            quality=InputQuality.DEGRADED,
            reason="restored_state_is_not_fresh_owner_evidence",
            updated_at=_updated_at(key, state),
        )
    raw_value = _attribute_value(key, state, raw_state)
    try:
        value, adapter_reason = _convert_value(
            key,
            raw_value,
            raw_state=raw_state,
            attributes=attributes,
            opening_safety_polarity=opening_safety_polarity,
        )
    except (TypeError, ValueError):
        return InputObservation(
            source=entity_id,
            quality=InputQuality.DEGRADED,
            reason="bound_entity_value_parse_error",
            updated_at=_updated_at(key, state),
        )
    explicit_quality = _explicit_quality(
        attributes,
        key=key,
        selected_value=value,
    )
    if explicit_quality is not None and explicit_quality is not InputQuality.FRESH:
        return InputObservation(
            source=entity_id,
            quality=explicit_quality,
            reason="owner_contract_quality_not_fresh",
            updated_at=_updated_at(key, state),
        )
    updated_at = _updated_at(key, state)
    quality, reason = _freshness(
        updated_at,
        now,
        freshness,
        owner_quality=explicit_quality,
    )
    return InputObservation(
        value=value if quality is InputQuality.FRESH or key != "private_time" else None,
        source=entity_id,
        quality=quality,
        reason=f"{adapter_reason};{_timestamp_reason(key, state)};{reason}",
        updated_at=updated_at,
    )


def _attribute_value(key: str, state: object, raw_state: object) -> object:
    attributes = getattr(state, "attributes", {}) or {}
    attribute_key = {
        "sun_elevation": "elevation",
        "sun_azimuth": "azimuth",
        "cover_position": "current_position",
        "privacy": "privacy_candidate",
        "indoor_temperature": "temperature",
        "cloud_cover": "cloud_coverage",
        "active_mode": "active_mode",
        "effective_target": "active_position",
    }.get(key)
    if key == "outdoor_temperature":
        if "outdoor_temperature" in attributes:
            attribute_key = "outdoor_temperature"
        elif _entity_domain(state) == "weather" and "temperature" in attributes:
            attribute_key = "temperature"
        elif attributes.get("contract") in {"weather_environment.v1", "outdoor_temperature"}:
            attribute_key = "temperature"
    if key == "indoor_temperature" and "temperature" not in attributes:
        if "current_temperature" in attributes:
            attribute_key = "current_temperature"
    if attribute_key and attribute_key in attributes:
        return attributes[attribute_key]
    return raw_state


def _entity_domain(state: object) -> str:
    return str(getattr(state, "entity_id", "")).split(".", 1)[0].lower()


def _convert_value(
    key: str,
    value: object,
    *,
    raw_state: object,
    attributes: Mapping[str, object],
    opening_safety_polarity: str,
) -> tuple[object, str]:
    if key == "away":
        return _convert_away(raw_state, attributes)
    if key == "activity_state":
        return _convert_activity(raw_state, attributes)
    if key == "private_time":
        return _convert_private_time(raw_state, attributes)
    if key == "day_state":
        normalized = str(raw_state).strip().lower()
        if normalized not in _CANONICAL_DAY_STATES:
            raise ValueError("day state is not canonical")
        return normalized, "canonical_nine_phase_day_state"
    if key == "day_context":
        return _convert_day_context(raw_state)
    if key == "cover_available":
        return _convert_cover_availability(raw_state)
    if key == "opening_safe_for_blind":
        if opening_safety_polarity == "unspecified":
            raise ValueError("opening safety polarity is not configured")
        active = _canonical_bool(value)
        if opening_safety_polarity == "negative_unsafe":
            return not active, "explicit_negative_unsafe_polarity_inverted"
        return active, "explicit_positive_safe_polarity"
    if key in {"safety_status", "apply_status"} and all(
        name in attributes for name in ("apply_enabled", "blockers")
    ):
        blockers = attributes["blockers"]
        blocked = (
            bool(blockers)
            if isinstance(blockers, (list, tuple, set))
            else _canonical_bool(blockers)
        )
        if key == "safety_status":
            return ("blocked" if blocked else "ready"), "legacy_debug_blocker_projection"
        apply_enabled = _canonical_bool(attributes["apply_enabled"])
        status = "blocked" if blocked else ("ready" if apply_enabled else "disabled")
        return status, "legacy_debug_apply_projection"
    if key in _BOOLEAN_KEYS:
        return _canonical_bool(value), "canonical_boolean_contract"
    if key in _NUMERIC_KEYS:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("numeric state is not finite")
        return result, "canonical_numeric_contract"
    return str(value), "canonical_state_contract"


def _canonical_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"on", "true", "yes", "1"}:
        return True
    if normalized in {"off", "false", "no", "0"}:
        return False
    raise ValueError("boolean state is not canonical")


def _true_bool(value: object) -> bool:
    try:
        return _canonical_bool(value)
    except (TypeError, ValueError):
        return False


def _convert_away(
    raw_state: object,
    attributes: Mapping[str, object],
) -> tuple[bool, str]:
    if "away_gate" in attributes:
        return _canonical_bool(attributes["away_gate"]), "core_state_away_gate_attribute"
    if isinstance(raw_state, bool):
        return raw_state, "canonical_away_boolean_state"
    normalized = str(raw_state).strip().lower()
    if normalized in {"away", "not_home", "abwesend"}:
        return True, "canonical_absent_presence_state"
    if normalized in {"home", "zuhause"}:
        return False, "canonical_home_presence_state"
    if normalized in {"on", "off", "true", "false", "yes", "no", "1", "0"}:
        return _canonical_bool(normalized), "controlled_boolean_presence_state"
    raise ValueError("presence state is not canonical")


def _convert_private_time(
    raw_state: object,
    attributes: Mapping[str, object],
) -> tuple[bool, str]:
    state_private = str(raw_state).strip().lower() == "private_time"
    if "private" not in attributes:
        return state_private, "core_state_private_time_state"
    attribute_private = _canonical_bool(attributes["private"])
    if state_private != attribute_private and state_private:
        raise ValueError("private-time state conflicts with owner attribute")
    return attribute_private, "core_state_private_attribute"


def _convert_day_context(raw_state: object) -> tuple[str, str]:
    normalized = str(raw_state).strip().lower()
    mapping = {
        "werktag": "weekday",
        "wochenende": "weekend",
        "frei": "holiday",
        "weekday": "weekday",
        "weekend": "weekend",
        "holiday": "holiday",
    }
    if normalized not in mapping:
        raise ValueError("day context is not canonical")
    return mapping[normalized], "canonical_day_context_adapter"


def _convert_cover_availability(raw_state: object) -> tuple[bool, str]:
    """Use HA entity availability, never the cover's open/closed position state."""

    normalized = str(raw_state).strip().lower()
    if normalized in {"open", "closed", "opening", "closing", "stopped"}:
        return True, "standard_cover_entity_is_available"
    return _canonical_bool(raw_state), "explicit_cover_availability_contract"


def _convert_activity(
    raw_state: object,
    attributes: Mapping[str, object],
) -> tuple[str, str]:
    """Adapt Core State activity evidence to blind-specific glare contexts."""

    state = str(raw_state).strip().lower()
    pc = _optional_bool_attribute(attributes, "pc_active")
    entertainment = _optional_bool_attribute(attributes, "entertainment_active")
    platform = str(attributes.get("gaming_platform", "")).strip().lower()
    context_values = {
        str(attributes.get(name, "")).strip().lower()
        for name in ("media_activity_context", "media_context")
        if attributes.get(name) not in (None, "")
    }

    tv_platforms = {"ps5", "playstation", "xbox", "switch", "tv"}
    pc_platforms = {"pc", "gaming_pc", "computer"}
    tv_contexts = {"entertainment", "tv", "streaming", "console", "gaming_tv"}
    pc_contexts = {"pc", "pc_active", "gaming_pc", "workstation"}
    general_contexts = {"screen", "display", "general_glare"}

    tv_active = (
        entertainment is True
        or platform in tv_platforms
        or state == "entertainment"
        or bool(context_values & tv_contexts)
    )
    pc_active = (
        pc is True
        or platform in pc_platforms
        or state == "pc_active"
        or bool(context_values & pc_contexts)
    )
    general_active = (
        state == "gaming"
        or bool(context_values & general_contexts)
        or (entertainment is True and not tv_active)
    )

    if tv_active:
        selected = "tv"
    elif pc_active:
        selected = "pc"
    elif general_active:
        selected = "screen"
    elif state in {
        "idle",
        "none",
        "music",
        "sleep",
        "waking",
        "private_time",
        "work_home",
        "work_away",
        "household",
        "free_time",
    }:
        selected = "none"
    else:
        raise ValueError("activity state has no documented blind glare mapping")

    evidence = ",".join(
        item
        for item in (
            f"state:{state}",
            "pc_active" if pc is True else "",
            "entertainment_active" if entertainment is True else "",
            f"platform:{platform}" if platform else "",
            *(f"context:{value}" for value in sorted(context_values)),
        )
        if item
    )
    return selected, f"core_state_glare_adapter_{selected}[{evidence}]"


def _optional_bool_attribute(attributes: Mapping[str, object], key: str) -> bool | None:
    if key not in attributes or attributes[key] is None:
        return None
    return _canonical_bool(attributes[key])


def _explicit_quality(
    attributes: Mapping[str, object], *, key: str | None = None, selected_value: object = None
) -> InputQuality | None:
    if key == "private_time":
        return _private_time_quality(attributes)
    if key == "activity_state":
        winner_quality = _activity_winner_quality(attributes, selected_value)
        if winner_quality is not None:
            return winner_quality
    field_quality = _field_quality_value(attributes, key)
    if field_quality is not _MISSING:
        return _parse_quality(field_quality)
    if key == "cover_ready" and _weather_quality_is_unrelated(attributes):
        for name in ("source_quality", "cover_ready_quality", "readiness_quality"):
            if name in attributes:
                return _parse_quality(attributes[name])
        return None
    value = attributes.get("quality_status", attributes.get("quality"))
    decision = attributes.get("activity_decision")
    if value is None and isinstance(decision, Mapping):
        value = decision.get("quality_status")
    if value is None and "source_quality" in attributes:
        value = attributes["source_quality"]
    if value is None and _true_bool(attributes.get("degraded")):
        return InputQuality.DEGRADED
    if value is None and "fresh" in attributes:
        try:
            return (
                InputQuality.FRESH if _canonical_bool(attributes["fresh"]) else InputQuality.STALE
            )
        except (TypeError, ValueError):
            return InputQuality.DEGRADED
    if value is None:
        return None
    return _parse_quality(value)


def _private_time_quality(attributes: Mapping[str, object]) -> InputQuality | None:
    """Read only field-specific Media/Private-Time quality evidence.

    Core State may publish an overall ``activity_decision.quality_status`` for
    unrelated inputs.  That status must not invalidate the canonical private
    attribute when the Media Activity feed itself is fresh.  Explicit
    private-time evidence still has precedence and remains blocking when it is
    stale, unavailable, degraded, or conflicting.
    """

    for name in (
        "private_time_quality",
        "private_quality",
        "private_time_freshness",
        "private_fresh",
        "media_activity_feed_quality",
        "media_activity_feed_freshness",
        "media_feed_quality",
        "media_feed_freshness",
    ):
        if name in attributes:
            return _parse_quality(_quality_marker_value(attributes[name]))

    for name in ("private_time_evidence", "private_evidence", "media_activity_feed"):
        evidence = attributes.get(name)
        if isinstance(evidence, Mapping):
            for marker in ("quality_status", "quality", "freshness", "status"):
                if marker in evidence:
                    return _parse_quality(_quality_marker_value(evidence[marker]))

    decision = attributes.get("activity_decision")
    if isinstance(decision, Mapping):
        candidates = decision.get("valid_candidates", decision.get("candidates"))
        if isinstance(candidates, Mapping):
            candidates = tuple(
                {"key": candidate_key, **candidate_value}
                for candidate_key, candidate_value in candidates.items()
                if isinstance(candidate_value, Mapping)
            )
        if isinstance(candidates, (list, tuple)):
            for candidate in candidates:
                if not isinstance(candidate, Mapping):
                    continue
                candidate_key = (
                    str(
                        candidate.get("key")
                        or candidate.get("candidate_key")
                        or candidate.get("context")
                        or ""
                    )
                    .strip()
                    .lower()
                )
                if candidate_key not in {"private", "private_time", "private_attribute"}:
                    continue
                for marker in ("quality_status", "quality", "freshness"):
                    if marker in candidate:
                        return _parse_quality(_quality_marker_value(candidate[marker]))

    # Backward-compatible direct owner markers remain field-local.  In
    # particular, do not read decision["quality_status"] here.
    for name in ("quality_status", "quality", "source_quality"):
        if name in attributes:
            return _parse_quality(_quality_marker_value(attributes[name]))
    if _true_bool(attributes.get("degraded")):
        return InputQuality.DEGRADED
    if "fresh" in attributes:
        try:
            return (
                InputQuality.FRESH if _canonical_bool(attributes["fresh"]) else InputQuality.STALE
            )
        except (TypeError, ValueError):
            return InputQuality.DEGRADED
    return None


_MISSING = object()


def _field_quality_value(attributes: Mapping[str, object], key: str | None) -> object:
    if key == "cover_ready":
        for name in (
            "cover_ready_quality",
            "readiness_quality",
            "cover_ready_fresh",
            "readiness_fresh",
        ):
            if name in attributes:
                return attributes[name]
        generic = attributes.get("quality_status", attributes.get("quality"))
        if str(generic).strip().lower() in {"weather_contract_degraded", "weather_degraded"}:
            return _MISSING
    return _MISSING


def _weather_quality_is_unrelated(attributes: Mapping[str, object]) -> bool:
    marker = str(attributes.get("quality_status", attributes.get("quality", ""))).strip().lower()
    return marker in {"weather_contract_degraded", "weather_degraded"}


def _parse_quality(value: object) -> InputQuality:
    normalized = str(value).strip().lower()
    if normalized in {"valid", "ok", "ready", "fresh", "healthy", "available", "operational"}:
        return InputQuality.FRESH
    try:
        return InputQuality(normalized)
    except ValueError:
        return InputQuality.DEGRADED


def _activity_winner_quality(
    attributes: Mapping[str, object], selected_value: object
) -> InputQuality | None:
    """Use quality for the selected activity evidence, not stale losers."""

    decision = attributes.get("activity_decision")
    selected = str(selected_value or "").strip().lower()
    if not isinstance(decision, Mapping):
        return None
    winner = decision.get("winner")
    winner_key = ""
    if isinstance(winner, Mapping):
        winner_key = (
            str(
                winner.get("key")
                or winner.get("candidate_key")
                or winner.get("context")
                or winner.get("value")
                or ""
            )
            .strip()
            .lower()
        )
        for name in ("quality_status", "quality", "freshness"):
            if name in winner:
                return _parse_quality(_quality_marker_value(winner[name]))
    elif winner is not None:
        winner_key = str(winner).strip().lower()

    candidates = decision.get("valid_candidates", decision.get("candidates"))
    if isinstance(candidates, Mapping):
        candidates = tuple(
            {"key": candidate_key, **candidate_value}
            for candidate_key, candidate_value in candidates.items()
            if isinstance(candidate_value, Mapping)
        )
    if isinstance(candidates, (list, tuple)):
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            values = {
                str(candidate.get(name, "")).strip().lower()
                for name in ("key", "candidate_key", "context", "variant", "value", "name")
            }
            if (winner_key and winner_key in values) or (selected and selected in values):
                for name in ("quality_status", "quality", "freshness"):
                    if name in candidate:
                        return _parse_quality(_quality_marker_value(candidate[name]))

    freshness = decision.get("freshness")
    input_sources = decision.get("input_sources")
    if isinstance(input_sources, Mapping) and isinstance(freshness, Mapping):
        for candidate_key, sources in input_sources.items():
            candidate_name = str(candidate_key).strip().lower()
            if not (
                candidate_name in {winner_key, selected}
                or winner_key in candidate_name
                or selected in candidate_name
            ):
                continue
            source_names = sources if isinstance(sources, (list, tuple, set)) else (sources,)
            markers = [
                _quality_marker_value(freshness[source])
                for source in source_names
                if source in freshness
            ]
            if markers:
                parsed = [_parse_quality(marker) for marker in markers]
                return next(
                    (quality for quality in parsed if quality is not InputQuality.FRESH),
                    InputQuality.FRESH,
                )
    if isinstance(freshness, Mapping):
        for name in (winner_key, selected):
            marker = freshness.get(name)
            if marker is not None:
                return _parse_quality(_quality_marker_value(marker))
    for name in ("activity_quality_status", "activity_quality", "activity_source_quality"):
        if name in attributes:
            return _parse_quality(attributes[name])
    return None


def _quality_marker_value(value: object) -> object:
    if isinstance(value, Mapping):
        return value.get("status", value.get("quality", value.get("quality_status", value)))
    return value


def _updated_at(key: str, state: object) -> datetime | None:
    if key == "cover_position":
        return _device_timestamp(state) or _ha_updated_at(state)
    return _ha_updated_at(state)


def _ha_updated_at(state: object) -> datetime | None:
    value = getattr(state, "last_updated", None) or getattr(state, "last_changed", None)
    return _as_utc_datetime(value)


def _device_timestamp(state: object) -> datetime | None:
    """Read an explicit source/device timestamp when the owner publishes one."""

    attributes = getattr(state, "attributes", {}) or {}
    for name in ("device_timestamp", "source_timestamp", "measurement_timestamp", "observed_at"):
        if name in attributes:
            timestamp = _as_utc_datetime(attributes[name])
            if timestamp is not None:
                return timestamp
    return None


def _timestamp_reason(key: str, state: object) -> str:
    if key != "cover_position":
        return "ha_state_timestamp_contract"
    if _device_timestamp(state) is not None:
        return "device_timestamp_contract"
    if _ha_updated_at(state) is not None:
        return "standard_cover_ha_timestamp_contract"
    return "timestamp_contract_missing"


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
    *,
    owner_quality: InputQuality | None = None,
) -> tuple[InputQuality, str]:
    if owner_quality is InputQuality.FRESH and policy.owner not in {
        "cover_device",
        "opening_owner",
        "technical_readiness",
    }:
        return InputQuality.FRESH, "owner_contract_quality_fresh_overrides_stable_ha_age"
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
