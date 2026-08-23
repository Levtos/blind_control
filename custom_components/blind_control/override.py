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
    guard is explicit and short-lived so an integration-owned movement and its
    attribute churn cannot become a manual override.
    """

    tolerance: float = 3.0
    baseline: float | None = None
    initialized: bool = False
    _writing_until: float = 0.0
    _writing_target: float | None = None
    _override: ManualOverride = ManualOverride()

    @classmethod
    def from_config(cls, config: BlindControlConfig) -> OverrideTracker:
        return cls(tolerance=config.position_tolerance)

    @property
    def override(self) -> ManualOverride:
        return self._override

    def on_restart(self, position: float | None) -> ManualOverride:
        """Establish a quiet-position baseline without inferring user intent."""

        self.baseline = _valid_position(position)
        self.initialized = self.baseline is not None
        self._writing_until = 0.0
        self._writing_target = None
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
        grace_seconds: float = 10.0,
    ) -> None:
        """Open a guard for an integration-owned movement observation."""

        if not 0 <= target <= 100:
            raise ValueError("target must be between 0 and 100")
        self._writing_target = target
        self._writing_until = (time.monotonic() if now is None else now) + grace_seconds

    def finish_own_write(self, position: float | None = None) -> None:
        """Close the guard after the owned movement has settled."""

        if position is not None:
            self.baseline = _valid_position(position)
            self.initialized = self.baseline is not None
        self._writing_until = 0.0
        self._writing_target = None

    def abort_own_write(self) -> None:
        """Close a guard after a command failed before the actuator accepted it."""

        self._writing_until = 0.0
        self._writing_target = None

    def observe_position(
        self,
        position: float | None,
        *,
        source: str = "cover_observation",
        now: float | None = None,
        observed_at: datetime | None = None,
    ) -> ManualOverride:
        """Process one position fact and return the current override state."""

        value = _valid_position(position)
        if value is None:
            return self._override
        if not self.initialized or self.baseline is None:
            self.baseline = value
            self.initialized = True
            return self._override

        current_time = time.monotonic() if now is None else now
        if current_time < self._writing_until:
            self.baseline = value
            if (
                self._writing_target is not None
                and abs(value - self._writing_target) <= self.tolerance
            ):
                self.finish_own_write(value)
            return self._override

        if abs(value - self.baseline) <= self.tolerance:
            return self._override

        self._override = ManualOverride(
            active=True,
            baseline=self.baseline,
            observed_position=value,
            source=source,
            reason="foreign_position_change_outside_writing_guard",
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
