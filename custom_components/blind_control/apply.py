"""Guarded Home Assistant cover writer for the AP3 Live boundary."""

from __future__ import annotations

import logging
import time
from dataclasses import replace

from .config import BlindControlConfig
from .contracts import ApplyDecision
from .shadow import ShadowRuntime, ShadowSnapshot

_LOGGER = logging.getLogger(__name__)

_COVER_DOMAIN = "cover"
_SET_POSITION_SERVICE = "set_cover_position"
_ENTITY_ID_FIELD = "entity_id"
_POSITION_FIELD = "position"
_READY_STATUSES = frozenset({"live_ready", "safety_ready"})


class CoverApplyExecutor:
    """Execute only an explicitly armed, already safety-approved target.

    The adapter owns no policy logic. Shadow mode, a non-Blind-Control owner,
    disabled Apply, restart baseline, manual override, Safety, and cooldown are
    all decided before this boundary is reached.
    """

    def __init__(
        self,
        hass: object,
        config: BlindControlConfig,
        runtime: ShadowRuntime,
    ) -> None:
        self.hass = hass
        self.config = config
        self.runtime = runtime

    async def async_apply(
        self,
        snapshot: ShadowSnapshot,
        *,
        now: float | None = None,
    ) -> ShadowSnapshot:
        """Dispatch one target or return an unchanged/blocked snapshot."""

        decision = snapshot.trace.apply
        if (
            not self._armed
            or snapshot is not self.runtime.latest_snapshot
            or decision.status not in _READY_STATUSES
        ):
            return snapshot
        target = decision.approved_target
        entity_id = dict(self.config.input_bindings).get("cover_position")
        if target is None or not _is_cover_entity_id(entity_id):
            return _replace_apply(
                snapshot,
                replace(
                    decision,
                    status="blocked",
                    reason="actuator_binding_not_cover",
                    approved_target=None,
                    write_path_reachable=False,
                ),
                actuation_executed=False,
                write_path_reachable=False,
            )
        services = getattr(self.hass, "services", None)
        async_call = getattr(services, "async_call", None)
        if not callable(async_call):
            return _replace_apply(
                snapshot,
                replace(
                    decision,
                    status="blocked",
                    reason="home_assistant_service_registry_unavailable",
                    approved_target=None,
                    write_path_reachable=False,
                ),
                actuation_executed=False,
                write_path_reachable=False,
            )

        monotonic_now = time.monotonic() if now is None else now
        self.runtime.begin_own_write(
            target,
            now=monotonic_now,
        )
        try:
            # No await between lifecycle validation and the service boundary.
            if not self._armed or snapshot is not self.runtime.latest_snapshot:
                return snapshot
            self.runtime.latest_snapshot = None  # Consume this approval exactly once.
            await async_call(
                _COVER_DOMAIN,
                _SET_POSITION_SERVICE,
                {
                    _ENTITY_ID_FIELD: entity_id,
                    _POSITION_FIELD: self.config.device_position(target),
                },
                blocking=False,
            )
        except Exception:  # Home Assistant integrations may raise arbitrary service errors.
            self.runtime.abort_own_write()
            self.runtime.cooldown_tracker.rollback_failed_write(target)
            _LOGGER.error("Blind Control cover apply failed; target remains unapplied")
            return _replace_apply(
                snapshot,
                replace(
                    decision,
                    status="error",
                    reason="cover_service_failed",
                    approved_target=None,
                    executed=False,
                ),
                actuation_executed=False,
                write_path_reachable=True,
            )

        self.runtime.cooldown_tracker.record_write(
            target, now=monotonic_now, cooldown_seconds=self.config.apply_cooldown_seconds
        )
        return _replace_apply(
            replace(snapshot, movement_status=self.runtime.override_tracker.motion_status),
            replace(
                decision,
                status="applied",
                reason="approved_target_dispatched",
                executed=True,
                write_path_reachable=True,
            ),
            actuation_executed=True,
            write_path_reachable=True,
        )

    @property
    def _armed(self) -> bool:
        return (
            self.runtime.active
            and self.runtime.config is self.config
            and self.config.runtime_mode == "live"
            and self.config.apply_owner == "blind_control"
            and self.config.apply_enabled
        )


def _replace_apply(
    snapshot: ShadowSnapshot,
    decision: ApplyDecision,
    *,
    actuation_executed: bool,
    write_path_reachable: bool,
) -> ShadowSnapshot:
    trace = replace(snapshot.trace, apply=decision)
    return replace(
        snapshot,
        trace=trace,
        actuation_executed=actuation_executed,
        write_path_reachable=write_path_reachable,
    )


def _is_cover_entity_id(value: object) -> bool:
    return isinstance(value, str) and value.startswith(f"{_COVER_DOMAIN}.") and len(value) > 6
