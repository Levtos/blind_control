"""Field-by-field legacy-to-shadow comparison without binding the old policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .contracts import DecisionTrace, InputObservation, InputQuality, LegacyEvidence


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
    legacy_quality: str = InputQuality.UNKNOWN.value
    legacy_source: str = "unbound"

    def as_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "legacy_value": self.legacy_value,
            "shadow_value": self.shadow_value,
            "classification": self.classification.value,
            "reason": self.reason,
            "legacy_quality": self.legacy_quality,
            "legacy_source": self.legacy_source,
        }


def compare_legacy_snapshot(
    legacy: Mapping[str, object] | LegacyEvidence | None,
    trace: DecisionTrace,
) -> tuple[ShadowDiff, ...]:
    """Compare real old-policy fields and classify every supplied observation."""

    if legacy is None:
        return ()
    if isinstance(legacy, LegacyEvidence):
        observations = legacy.as_mapping()
    else:
        observations = {
            key: InputObservation(
                value=value,
                source="legacy_mapping",
                quality=InputQuality.FRESH,
                reason="explicit_legacy_mapping",
            )
            for key, value in legacy.items()
        }
    shadow_values = {
        "active_mode": trace.active_mode,
        "effective_target": trace.effective_target,
        "safety_status": trace.safety.status,
        "apply_status": trace.apply.status,
    }
    diffs: list[ShadowDiff] = []
    for field, shadow_value in shadow_values.items():
        if field not in observations:
            continue
        observation = observations[field]
        legacy_value = observation.value
        if not observation.usable:
            classification = DiffClassification.ERROR
            reason = "legacy_field_evidence_not_fresh"
        elif legacy_value == shadow_value:
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
                legacy_quality=observation.quality.value,
                legacy_source=observation.source,
            )
        )
    return tuple(diffs)
