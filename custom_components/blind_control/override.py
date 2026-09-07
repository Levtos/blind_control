"""Pure override lifecycle with a restart-safe writing guard."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from .config import BlindControlConfig
from .contracts import ManualOverride, OverrideContextKey


@dataclass(slots=True)
class OverrideTracker:
    """Track only proven foreign position changes.

    The tracker observes facts and never performs a device write.  A writing
    guard ends only on stable target evidence so an integration-owned movement and its
    attribute churn cannot become a manual override.
    """

    tolerance: float = 3.0
    settle_seconds: float = 2.0
    timeout_seconds: float = 120.0
    motion_status: str = "idle"
    _quiet_position: float | None = None
    _quiet_since: float | None = None
    baseline: float | None = None
    initialized: bool = False
    _writing_until: float = 0.0
    _writing_target: float | None = None
    _override: ManualOverride = ManualOverride()

    @classmethod
    def from_config(cls, config: BlindControlConfig) -> OverrideTracker:
        return cls(
            tolerance=config.position_tolerance,
            settle_seconds=config.position_settle_seconds,
            timeout_seconds=config.movement_timeout_seconds,
        )

    @property
    def override(self) -> ManualOverride:
        return self._override

    @property
    def own_target(self) -> float | None:
        return self._writing_target

    def on_restart(self, position: float | None) -> ManualOverride:
        """Establish a quiet-position baseline without inferring user intent."""

        self.baseline = _valid_position(position)
        self.initialized = self.baseline is not None
        self._writing_until = 0.0
        self._writing_target = None
        self._quiet_position = None
        self._quiet_since = None
        self.motion_status = "idle" if self.initialized else "baseline_pending"
        self._override = ManualOverride.inactive("restart_baseline_established")
        return self._override

    def on_configuration_change(self, position: float | None = None) -> ManualOverride:
        """Rebase configuration changes without creating a manual override."""

        if position is not None:
            self.baseline = _valid_position(position)
            self.initialized = self.baseline is not None
        if not self._override.active:
            self._override = ManualOverride.inactive("configuration_changed")
        return self._override

    def begin_own_write(
        self,
        target: float,
        *,
        now: float | None = None,
        grace_seconds: float | None = None,
    ) -> None:
        """Open a guard for an integration-owned movement observation."""

        if not 0 <= target <= 100:
            raise ValueError("target must be between 0 and 100")
        self._writing_target = target
        self._writing_until = (time.monotonic() if now is None else now) + (
            self.timeout_seconds if grace_seconds is None else grace_seconds
        )
        self._quiet_position = None
        self._quiet_since = None
        self.motion_status = "own_moving"

    def finish_own_write(self, position: float | None = None) -> None:
        """Close the guard after the owned movement has settled."""

        if position is not None:
            self.baseline = _valid_position(position)
            self.initialized = self.baseline is not None
        self._writing_until = 0.0
        self._writing_target = None
        self.motion_status = "idle"

    def abort_own_write(self) -> None:
        """Retain attribution after an ambiguous service failure."""

        # An error is not proof that the device rejected the command.
        # Retain attribution until its actual target is stably reached.
        self.motion_status = "command_error"

    def observe_position(
        self,
        position: float | None,
        *,
        source: str = "cover_observation",
        now: float | None = None,
        observed_at: datetime | None = None,
        moving: bool = False,
    ) -> ManualOverride:
        """Process one position fact and return the current override state."""

        value = _valid_position(position)
        if value is None:
            self._quiet_position = None
            self._quiet_since = None
            self.motion_status = "position_unavailable"
            return self._override
        current_time = time.monotonic() if now is None else now
        if moving:
            self._quiet_position = None
            self._quiet_since = None
            self.motion_status = (
                "target_not_reached"
                if self._writing_target is not None and current_time >= self._writing_until
                else "own_moving"
                if self._writing_target is not None
                else "external_moving"
                if self.initialized
                else "baseline_pending"
            )
            return self._override
        if self._quiet_position is None or abs(value - self._quiet_position) > self.tolerance:
            self._quiet_position = value
            self._quiet_since = current_time
        settled = (
            self._quiet_since is not None
            and current_time - self._quiet_since >= self.settle_seconds
        )
        if self._writing_target is not None:
            if abs(value - self._writing_target) <= self.tolerance and settled:
                self.finish_own_write(value)
            else:
                self.motion_status = (
                    "target_not_reached" if current_time >= self._writing_until else "own_settling"
                )
            return self._override
        if not settled:
            self.motion_status = "settling" if self.initialized else "baseline_pending"
            return self._override
        self.motion_status = "idle"
        if not self.initialized or self.baseline is None:
            self.baseline = value
            self.initialized = True
            return self._override

        if abs(value - self.baseline) <= self.tolerance:
            return self._override

        self._override = ManualOverride(
            active=True,
            baseline=self.baseline,
            observed_position=value,
            source=source,
            reason="foreign_position_change_after_settling",
            started_at=observed_at or datetime.now(UTC),
        )
        return self._override

    def attach_context(self, context_key: OverrideContextKey) -> ManualOverride:
        """Bind an active foreign override to the explicit evaluation context."""

        if self._override.active:
            self._override = replace(self._override, context_key=context_key)
        return self._override

    def clear(self, reason: str = "cleared") -> ManualOverride:
        """Clear and rebase on the last observed foreign position."""

        if self._override.active and self._override.observed_position is not None:
            self.baseline = self._override.observed_position
            self.initialized = True
        self._override = ManualOverride.inactive(reason)
        return self._override


def _valid_position(position: float | None) -> float | None:
    if position is None:
        return None
    if isinstance(position, bool) or not 0 <= float(position) <= 100:
        raise ValueError("cover position must be between 0 and 100")
    return float(position)
