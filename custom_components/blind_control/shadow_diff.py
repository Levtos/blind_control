"""Field-by-field legacy-to-shadow comparison without binding the old policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .contracts import DecisionTrace


class DiffClassification(StrEnum):
    EXPECTED = "expected"
    IMPROVED = "improved"
    UNRESOLVED = "unresolved"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ShadowDiff:
    field: str
    legacy_value: object
    shadow_value: object
    classification: DiffClassification
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "legacy_value": self.legacy_value,
            "shadow_value": self.shadow_value,
            "classification": self.classification.value,
            "reason": self.reason,
        }


def compare_legacy_snapshot(
    legacy: Mapping[str, object] | None,
    trace: DecisionTrace,
) -> tuple[ShadowDiff, ...]:
    """Compare only supplied legacy fields; missing legacy evidence is explicit."""

    if legacy is None:
        return ()
    shadow_values = {
        "active_mode": trace.active_mode,
        "effective_target": trace.effective_target,
        "safety_status": trace.safety.status,
        "apply_status": trace.apply.status,
    }
    diffs: list[ShadowDiff] = []
    for field, shadow_value in shadow_values.items():
        if field not in legacy:
            continue
        legacy_value = legacy[field]
        if legacy_value == shadow_value:
            classification = DiffClassification.EXPECTED
            reason = "field_matches_shadow_decision"
        elif field == "safety_status" and trace.safety.status == "blocked":
            classification = DiffClassification.IMPROVED
            reason = "shadow_preserves_safety_block_instead_of_unsafe_fallback"
        elif field == "effective_target" and shadow_value is None:
            classification = DiffClassification.IMPROVED
            reason = "shadow_refuses_target_without_positive_evidence"
        else:
            classification = DiffClassification.UNRESOLVED
            reason = "field_diff_requires_trace_review_before_cutover"
        diffs.append(
            ShadowDiff(
                field=field,
                legacy_value=legacy_value,
                shadow_value=shadow_value,
                classification=classification,
                reason=reason,
            )
        )
    return tuple(diffs)
