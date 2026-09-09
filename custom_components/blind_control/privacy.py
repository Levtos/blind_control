"""Privacy demand from the canonical Core-State day phase, without a local clock."""

from dataclasses import replace

from .contracts import BlindControlInputs, InputQuality

PRIVACY_PHASES = frozenset({"evening", "late_evening", "early_night", "late_night"})
DAY_PHASES = PRIVACY_PHASES | {"early_morning", "forenoon", "midday", "afternoon", "late_afternoon"}


def with_phase_privacy(inputs: BlindControlInputs) -> BlindControlInputs:
    """Replace the retired boolean binding; retain source quality and provenance."""

    day = inputs.day_state
    valid = day.usable and day.value in DAY_PHASES
    return replace(
        inputs,
        privacy=replace(
            day,
            value=day.value in PRIVACY_PHASES if valid else None,
            quality=day.quality if valid or not day.usable else InputQuality.CONFLICT,
            reason="privacy_from_core_state_day_phase" if valid else "privacy_day_phase_unusable",
            evidence=(("rule", "blind_control.privacy_phase.v1"), ("input", "day_state")),
        ),
    )
