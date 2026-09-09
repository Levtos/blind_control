"""Typed dimensions and arbitration; no actuator, clock or alternate policy owner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal


@dataclass(frozen=True, slots=True)
class CanonicalFact:
    key: str
    value: object
    quality: str
    owner: str
    timestamp_basis: str
    observed_at: str | None
    source_revision: str | None
    reason: str
    details: tuple[tuple[str, str | bool], ...] = ()


@dataclass(frozen=True, slots=True)
class ContextIntent:
    mode: str = "neutral"
    variant: str | None = None
    base_target: float | None = None


@dataclass(frozen=True, slots=True)
class DecisionIssue:
    feature: str
    evidence: str
    quality: str
    owner: str
    timestamp_basis: str
    reason: str
    fallback: str = "no_positive_evidence"
    severity: str = "feature_degraded"


@dataclass(frozen=True, slots=True)
class Contribution:
    feature: str
    variant: str | None
    effect: Literal["max_open", "min_open", "hold", "block_direction", "open_reason"]
    value: float | None
    status: str
    reason: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SafetyEnvelope:
    min_open: float = 0.0
    block_direction: str | None = None
    status: str = "pending"
    reason: str = "not_evaluated"


@dataclass(frozen=True, slots=True)
class Constraint:
    effect: Literal["max_open", "min_open", "hold", "block_direction"]
    value: float | str | None
    scope: str
    status: str = "active"


@dataclass(frozen=True, slots=True)
class DimensionalDecision:
    """Authoritative target, with additive identity and legacy projection outside."""

    context: ContextIntent
    contributions: tuple[Contribution, ...]
    issues: tuple[DecisionIssue, ...]
    evidence: tuple[CanonicalFact, ...] = ()
    safety: SafetyEnvelope = SafetyEnvelope()
    feasible_interval: tuple[float, float] = (0.0, 100.0)
    target_position: float | None = None
    decision_id: str = "pure"
    decision_generation: int = 0
    runtime_generation: int = 0
    config_revision: str = ""
    snapshot_identity: str = "pure"
    evaluated_at: str | None = None
    runtime_status: str = "unarmed"
    apply_status: str = "not_evaluated"
    lease_status: str = "unarmed"
    version: str = "blind_control.dimensions.v1"

    def arbitrate(self, *, control_hold: float | None = None) -> DimensionalDecision:
        caps = [
            item.value
            for item in self.contributions
            if item.status == "active" and item.effect == "max_open" and item.value is not None
        ]
        ceiling = min(caps, default=100.0)
        base = self.context.base_target
        if control_hold is not None:
            base = control_hold
        proven_caps = [
            item.value
            for item in self.contributions
            if item.status == "active"
            and item.effect == "max_open"
            and item.value is not None
            and item.reason != "quality_loss_blocks_only_opening"
        ]
        if base is None and proven_caps:
            base = min(proven_caps)
        # Relief is positive opening evidence only without a closing request.
        if not proven_caps and self.context.mode in {"neutral", "daylight"}:
            openings = [
                item.value
                for item in self.contributions
                if item.status == "active"
                and item.effect == "open_reason"
                and item.value is not None
            ]
            base = min(([base] if base is not None else []) + openings, default=None)
        floor = self.safety.min_open
        if base is None and self.safety.status == "safe_position":
            base = floor  # Positive hard-safety evidence may itself require opening.
        contributions = tuple(
            replace(item, status="suppressed", reason="hard_safety_min_open")
            if item.status == "active"
            and item.effect == "max_open"
            and item.value is not None
            and item.value < floor
            else item
            for item in self.contributions
        )
        return replace(
            self,
            contributions=contributions,
            feasible_interval=(floor, max(floor, ceiling)),
            target_position=max(floor, min(base, ceiling)) if base is not None else None,
        )

    def as_dict(self) -> dict[str, object]:
        constraints = [
            Constraint(item.effect, item.value, item.feature, item.status)
            for item in self.contributions
            if item.effect != "open_reason"
        ]
        constraints.append(Constraint("min_open", self.safety.min_open, "hard_safety"))
        if self.safety.block_direction is not None:
            constraints.append(
                Constraint("block_direction", self.safety.block_direction, "hard_safety")
            )
        if self.target_position is None:
            constraints.append(Constraint("hold", None, "decision"))
        return {**asdict(self), "constraints": [asdict(item) for item in constraints]}
