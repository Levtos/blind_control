"""Latest-target-only cooldown state for the future Apply boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CooldownDecision:
    """Result of proposing a target to the pure cooldown tracker."""

    apply_now: bool
    target: float | None
    pending_target: float | None
    reason: str


@dataclass(slots=True)
class CooldownTracker:
    """Keep only the newest target while an automatic cooldown is active."""

    tolerance: float = 3.0
    last_applied_target: float | None = None
    cooldown_until: float = 0.0
    pending_target: float | None = None

    def propose(
        self,
        target: float | None,
        *,
        now: float,
        cooldown_seconds: float,
        bypass_cooldown: bool = False,
    ) -> CooldownDecision:
        if target is None:
            self.pending_target = None
            return CooldownDecision(False, None, None, "no_target")
        if (
            self.last_applied_target is not None
            and abs(target - self.last_applied_target) <= self.tolerance
            and self.pending_target is None
        ):
            return CooldownDecision(False, None, None, "identical_target")
        if not bypass_cooldown and now < self.cooldown_until:
            self.pending_target = target
            return CooldownDecision(
                False, None, self.pending_target, "cooldown_active_latest_target_saved"
            )

        self.last_applied_target = target
        self.pending_target = None
        self.cooldown_until = now + max(0.0, cooldown_seconds)
        return CooldownDecision(
            True,
            target,
            None,
            "safety_target_ready" if bypass_cooldown else "target_ready",
        )

    def rollback_failed_write(self, target: float) -> None:
        """Make a failed command immediately retryable without reviving old targets."""

        if self.last_applied_target == target:
            self.last_applied_target = None
        self.cooldown_until = 0.0
        self.pending_target = None

    def release(self, *, now: float, cooldown_seconds: float) -> CooldownDecision:
        if self.pending_target is None:
            return CooldownDecision(False, None, None, "no_pending_target")
        if now < self.cooldown_until:
            return CooldownDecision(
                False,
                None,
                self.pending_target,
                "cooldown_active_latest_target_saved",
            )

        target = self.pending_target
        self.pending_target = None
        self.last_applied_target = target
        self.cooldown_until = now + max(0.0, cooldown_seconds)
        return CooldownDecision(True, target, None, "latest_target_released")

    def as_dict(self) -> dict[str, float | None]:
        return {
            "last_applied_target": self.last_applied_target,
            "cooldown_until": self.cooldown_until,
            "pending_target": self.pending_target,
        }
