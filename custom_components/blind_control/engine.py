"""Deterministic Blind Control decision tree for AP2 Shadow mode."""

from __future__ import annotations

from dataclasses import replace

from .config import BlindControlConfig
from .contracts import (
    ApplyDecision,
    BlindControlInputs,
    Candidate,
    DecisionBranch,
    DecisionTrace,
    DecisionWinner,
    FailureDecision,
    InputObservation,
    InputQuality,
    ManualOverride,
    MasterMode,
    OpeningState,
    PausedRequirement,
    QualityBlocker,
    SafetyDecision,
    SolarExposure,
    SolarExposureState,
)
from .cooldown import CooldownTracker
from .solar import calculate_solar_exposure

DECISION_CONTRACT_VERSION = "blind_control.decision.v2"
DAYLIGHT_STATES = frozenset(
    {"dawn", "morning", "day", "midday", "afternoon", "late_afternoon", "evening"}
)
SCREEN_ACTIVITY = frozenset({"screen", "glare", "general_glare"})
TV_ACTIVITY = frozenset({"tv", "console", "streaming", "playstation", "xbox", "switch"})
PC_ACTIVITY = frozenset({"pc", "computer", "workstation"})
OPENING_CANDIDATES = frozenset({"base_daylight", "storm_approaching", "cool_air_available"})
AUTOMATIC_DECISION_QUALITY_INPUTS = (
    "bio_state",
    "activity_state",
    "day_state",
    "day_context",
    "away",
    "private_time",
    "privacy",
    "indoor_temperature",
    "outdoor_temperature",
    "outdoor_lux",
    "lux_trend",
    "sun_elevation",
    "sun_azimuth",
    "expected_direct_radiation",
    "expected_diffuse_radiation",
    "cloud_cover",
)


class DecisionEngine:
    """Calculate policy intent without owning an actuator or a Home Assistant API."""

    def __init__(self, config: BlindControlConfig | None = None) -> None:
        self.config = config or BlindControlConfig.defaults()

    def evaluate(
        self,
        inputs: BlindControlInputs,
        *,
        override: ManualOverride | None = None,
        now: float | None = None,
        cooldown: CooldownTracker | None = None,
        failure_hold_target: float | None = None,
    ) -> DecisionTrace:
        override = override or ManualOverride.inactive()
        solar = calculate_solar_exposure(inputs, self.config)
        candidates: list[Candidate] = []
        paused: list[PausedRequirement] = []

        waking = _is_value(inputs.bio_state, "waking")
        candidates.append(self._base_candidate(inputs))
        candidates.extend(self._mode_candidates(inputs, waking=waking, override=override))

        environment = self._environment_candidates(inputs, solar)
        if waking:
            for candidate in environment:
                if candidate.key in {
                    "heat_protection",
                    "glare_general",
                    "glare_tv",
                    "glare_pc",
                    "cold_insulation",
                }:
                    if candidate.active:
                        paused.append(
                            PausedRequirement(
                                key=candidate.key,
                                reason="waking_exclusive_until_awake",
                                source=inputs.bio_state.source,
                            )
                        )
                        candidates.append(replace(candidate, paused=True, suppressed_by="waking"))
                    else:
                        candidates.append(candidate)
                else:
                    candidates.append(candidate)
        else:
            candidates.extend(environment)

        if override.active and override.observed_position is not None and not waking:
            held_candidates: list[Candidate] = []
            for candidate in candidates:
                if candidate.active and candidate.key != "manual_override":
                    paused.append(
                        PausedRequirement(
                            key=candidate.key,
                            reason="manual_override_holds_automation",
                            source=override.source,
                        )
                    )
                    held_candidates.append(
                        replace(candidate, paused=True, suppressed_by="manual_override")
                    )
                else:
                    held_candidates.append(candidate)
            candidates = held_candidates

        known_paused = {item.key for item in paused}
        for candidate in candidates:
            if candidate.active and candidate.paused and candidate.key not in known_paused:
                paused.append(
                    PausedRequirement(
                        key=candidate.key,
                        reason=candidate.suppressed_by or "exclusive_mode",
                        source=candidate.source,
                    )
                )

        active = [
            candidate
            for candidate in candidates
            if candidate.active and not candidate.paused and candidate.target_position is not None
        ]
        closing_active = [
            candidate for candidate in active if candidate.key not in OPENING_CANDIDATES
        ]
        selected = closing_active or active
        fachlicher_target = min(
            (
                candidate.target_position
                for candidate in selected
                if candidate.target_position is not None
            ),
            default=None,
        )
        winner_keys = tuple(
            candidate.key
            for candidate in selected
            if candidate.target_position is not None
            and fachlicher_target is not None
            and candidate.target_position == fachlicher_target
        )
        active_mode = self._active_mode(candidates, waking=waking)
        winner = self._winner(candidates, winner_keys, fachlicher_target)
        active_branches = tuple(
            DecisionBranch.from_candidate(
                candidate,
                winner=winner is not None and candidate.key == winner.candidate_key,
            )
            for candidate in candidates
            if candidate.active
        )
        failure = self._failure(inputs, failure_hold_target)
        master_mode = self._master_mode(override=override, waking=waking, failure=failure)
        safety = self._safety(inputs, fachlicher_target)
        effective_target = safety.approved_target
        if safety.status == "ready":
            effective_target = fachlicher_target
        if failure.active and safety.status == "safe_position":
            failure = replace(
                failure,
                status="safety_position",
                hold_target=safety.approved_target,
            )
        elif failure.active:
            effective_target = failure.hold_target

        apply = (
            self._failure_apply(failure, effective_target)
            if failure.active and safety.status != "safe_position"
            else self._apply(
                effective_target=effective_target,
                safety=safety,
                override=override,
                cooldown=cooldown,
                now=0.0 if now is None else now,
            )
        )
        reasons = list(self._reasons(candidates, paused, fachlicher_target, failure, safety, apply))
        return DecisionTrace(
            version=DECISION_CONTRACT_VERSION,
            candidates=tuple(candidates),
            paused_requirements=tuple(paused),
            winner_keys=winner_keys,
            fachlicher_target=fachlicher_target,
            effective_target=effective_target,
            active_mode=active_mode,
            master_mode=master_mode,
            winner=winner,
            active_branches=active_branches,
            failure=failure,
            solar=solar,
            safety=safety,
            apply=apply,
            override=override,
            reasons=tuple(reasons),
        )

    def _base_candidate(self, inputs: BlindControlInputs) -> Candidate:
        quality = _quality(inputs.day_state, inputs.day_context)
        if not inputs.day_state.usable or not inputs.day_context.usable:
            return self._candidate(
                "base_daylight",
                "neutral",
                False,
                None,
                _source(inputs.day_state, inputs.day_context),
                "positive_daylight_reason_missing_or_not_fresh",
                quality,
            )
        day_state = str(inputs.day_state.value).lower()
        if day_state in DAYLIGHT_STATES:
            return self._candidate(
                "base_daylight",
                "neutral",
                True,
                self.config.target("open"),
                inputs.day_state.source,
                "canonical_day_state_is_daylight",
                InputQuality.FRESH,
            )
        return self._candidate(
            "neutral_context",
            "neutral",
            True,
            None,
            inputs.day_state.source,
            "known_non_daylight_neutral_context",
            InputQuality.FRESH,
        )

    def _mode_candidates(
        self,
        inputs: BlindControlInputs,
        *,
        waking: bool,
        override: ManualOverride,
    ) -> list[Candidate]:
        candidates = [
            self._candidate(
                "sleep",
                "sleep",
                _is_value(inputs.bio_state, "sleep"),
                self.config.target("sleep") if _is_value(inputs.bio_state, "sleep") else None,
                inputs.bio_state.source,
                "canonical_bio_state_sleep"
                if _is_value(inputs.bio_state, "sleep")
                else "bio_state_not_sleep",
                inputs.bio_state.quality,
            ),
            self._candidate(
                "waking",
                "waking",
                waking,
                self.config.target("waking") if waking else None,
                inputs.bio_state.source,
                "canonical_waking_exclusive_until_awake" if waking else "bio_state_not_waking",
                inputs.bio_state.quality,
            ),
            self._candidate(
                "away",
                "away",
                inputs.away.usable and bool(inputs.away.value),
                self.config.target("away") if inputs.away.usable and inputs.away.value else None,
                inputs.away.source,
                "canonical_away_active"
                if inputs.away.usable and inputs.away.value
                else "away_not_active",
                inputs.away.quality,
            ),
            self._candidate(
                "private_time",
                "privacy",
                inputs.private_time.usable and bool(inputs.private_time.value),
                self.config.target("private_time")
                if inputs.private_time.usable and inputs.private_time.value
                else None,
                inputs.private_time.source,
                "private_time_active"
                if inputs.private_time.usable and inputs.private_time.value
                else "private_time_not_active",
                inputs.private_time.quality,
                variant="private_time",
            ),
        ]
        privacy_active = inputs.privacy.usable and bool(inputs.privacy.value)
        candidates.append(
            self._candidate(
                "privacy",
                "privacy",
                privacy_active,
                self.config.target("privacy") if privacy_active else None,
                inputs.privacy.source,
                "privacy_active" if privacy_active else "privacy_not_active",
                inputs.privacy.quality,
                paused=waking and privacy_active,
                suppressed_by="waking" if waking and privacy_active else None,
            )
        )
        if override.active and override.observed_position is not None:
            candidates.append(
                self._candidate(
                    "manual_override",
                    "override",
                    True,
                    override.observed_position,
                    override.source,
                    "proven_foreign_position_change",
                    InputQuality.FRESH,
                    paused=waking,
                    suppressed_by="waking" if waking else None,
                )
            )
        else:
            candidates.append(
                self._candidate(
                    "manual_override",
                    "override",
                    False,
                    None,
                    override.source,
                    "no_proven_foreign_position_change",
                    InputQuality.UNKNOWN,
                )
            )
        return candidates

    def _environment_candidates(
        self,
        inputs: BlindControlInputs,
        solar: SolarExposure,
    ) -> list[Candidate]:
        storm = self._storm_active(inputs)
        heat, heat_reason = self._heat_active(inputs, solar, storm)
        glare_relevant = self._glare_relevant(solar)
        glare_general = glare_relevant and _activity(inputs, SCREEN_ACTIVITY)
        glare_tv = glare_relevant and _activity(inputs, TV_ACTIVITY)
        glare_pc = glare_relevant and _activity(inputs, PC_ACTIVITY)
        cold = self._cold_active(inputs, solar)
        cool_air = self._cool_air_active(inputs)
        return [
            self._candidate(
                "heat_protection",
                "climate",
                heat,
                self.config.target("heat_protection") if heat else None,
                _source(inputs.outdoor_temperature, solar),
                heat_reason,
                _quality(inputs.outdoor_temperature, inputs.indoor_temperature),
                variant="heat",
            ),
            self._candidate(
                "glare_general",
                "glare",
                glare_general,
                self.config.target("glare_general") if glare_general else None,
                inputs.activity_state.source,
                "screen_activity_with_window_solar_relevance"
                if glare_general
                else "screen_activity_without_window_solar_relevance"
                if _activity(inputs, SCREEN_ACTIVITY) and not glare_relevant
                else "no_general_glare_activity",
                inputs.activity_state.quality,
                variant="general",
            ),
            self._candidate(
                "glare_tv",
                "glare",
                glare_tv,
                self.config.target("glare_tv") if glare_tv else None,
                inputs.activity_state.source,
                "tv_or_console_with_window_solar_relevance"
                if glare_tv
                else "tv_activity_without_window_solar_relevance"
                if _activity(inputs, TV_ACTIVITY) and not glare_relevant
                else "no_tv_activity",
                inputs.activity_state.quality,
                variant="tv",
            ),
            self._candidate(
                "glare_pc",
                "glare",
                glare_pc,
                self.config.target("glare_pc") if glare_pc else None,
                inputs.activity_state.source,
                "pc_activity_with_window_solar_relevance"
                if glare_pc
                else "pc_activity_without_window_solar_relevance"
                if _activity(inputs, PC_ACTIVITY) and not glare_relevant
                else "no_pc_activity",
                inputs.activity_state.quality,
                variant="pc",
            ),
            self._candidate(
                "storm_approaching",
                "climate",
                storm,
                self.config.target("storm_approaching") if storm else None,
                _source(inputs.weather_alert, inputs.precipitation_trend, inputs.wind_trend),
                "multiple_weather_trend_signals" if storm else "insufficient_storm_signals",
                _quality(inputs.weather_alert, inputs.precipitation_trend, inputs.wind_trend),
                variant="storm",
            ),
            self._candidate(
                "cool_air_available",
                "climate",
                cool_air,
                self.config.target("cool_air_available") if cool_air else None,
                _source(inputs.indoor_temperature, inputs.outdoor_temperature, inputs.air_movement),
                "cooler_moving_outdoor_air_available" if cool_air else "cool_air_not_proven",
                _quality(
                    inputs.indoor_temperature, inputs.outdoor_temperature, inputs.air_movement
                ),
                variant="cool_air",
            ),
            self._candidate(
                "cold_insulation",
                "climate",
                cold,
                self.config.target("cold_insulation") if cold else None,
                _source(inputs.outdoor_temperature, solar),
                "dark_cold_without_solar_gain" if cold else "cold_insulation_conditions_not_met",
                _quality(inputs.outdoor_temperature, inputs.opening_state),
                variant="cold",
            ),
        ]

    def _glare_relevant(self, solar: SolarExposure) -> bool:
        """Use an independent window-solar signal for screen glare."""

        return (
            solar.state
            in {
                SolarExposureState.DIRECT_SUN,
                SolarExposureState.CLOUD_SHADOW,
                SolarExposureState.DIFFUSE_BRIGHT,
            }
            and solar.confidence >= self.config.glare_confidence_threshold
        )

    def _heat_active(
        self,
        inputs: BlindControlInputs,
        solar: SolarExposure,
        storm: bool,
    ) -> tuple[bool, str]:
        if not inputs.indoor_temperature.usable and not inputs.outdoor_temperature.usable:
            return False, "heat_temperature_not_fresh"
        thermal_load = (
            inputs.outdoor_temperature.usable
            and float(inputs.outdoor_temperature.value) >= self.config.heat_outdoor_threshold
        ) or (
            inputs.indoor_temperature.usable
            and float(inputs.indoor_temperature.value) >= self.config.heat_indoor_threshold
        )
        solar_possible = solar.state in {
            SolarExposureState.DIRECT_SUN,
            SolarExposureState.CLOUD_SHADOW,
            SolarExposureState.DIFFUSE_BRIGHT,
        }
        if storm:
            return False, "storm_approaching_relaxes_heat"
        if (
            thermal_load
            and solar_possible
            and solar.confidence >= self.config.heat_confidence_threshold
        ):
            return True, "thermal_load_with_window_solar_relevance"
        if not thermal_load:
            return False, "thermal_load_below_configured_band"
        if not solar_possible:
            return False, "solar_exposure_not_relevant_for_heat"
        return False, "solar_confidence_below_configured_band"

    def _storm_active(self, inputs: BlindControlInputs) -> bool:
        signals = 0
        if inputs.weather_alert.usable and bool(inputs.weather_alert.value):
            signals += 1
        if (
            inputs.precipitation_trend.usable
            and float(inputs.precipitation_trend.value)
            > self.config.storm_precipitation_trend_threshold
        ):
            signals += 1
        if (
            inputs.wind_trend.usable
            and float(inputs.wind_trend.value) > self.config.storm_wind_trend_threshold
        ):
            signals += 1
        if (
            inputs.pressure_trend.usable
            and float(inputs.pressure_trend.value) < -self.config.storm_pressure_drop_threshold
        ):
            signals += 1
        if (
            inputs.lux_trend.usable
            and float(inputs.lux_trend.value) <= -self.config.cloud_shadow_lux_drop
        ):
            signals += 1
        return signals >= self.config.storm_required_signals

    def _cool_air_active(self, inputs: BlindControlInputs) -> bool:
        return (
            inputs.indoor_temperature.usable
            and inputs.outdoor_temperature.usable
            and inputs.air_movement.usable
            and bool(inputs.air_movement.value)
            and float(inputs.indoor_temperature.value) - float(inputs.outdoor_temperature.value)
            >= self.config.cool_air_delta
        )

    def _cold_active(self, inputs: BlindControlInputs, solar: SolarExposure) -> bool:
        return (
            inputs.outdoor_temperature.usable
            and float(inputs.outdoor_temperature.value) <= self.config.cold_outdoor_threshold
            and solar.state in {SolarExposureState.NIGHT, SolarExposureState.SOLAR_NOT_ON_WINDOW}
        )

    def _safety(
        self,
        inputs: BlindControlInputs,
        fachlicher_target: float | None,
    ) -> SafetyDecision:
        opening = _opening(inputs.opening_state)
        if not inputs.opening_state.usable:
            return SafetyDecision(
                status="blocked",
                reason="opening_contract_not_fresh_positive_evidence_required",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.opening_state.source,
            )
        if opening is OpeningState.OPEN:
            if not inputs.cover_available.usable or not inputs.cover_available.value:
                return SafetyDecision(
                    status="blocked",
                    reason="cover_availability_not_fresh_and_positive",
                    approved_target=None,
                    opening_state=opening.value,
                    source=inputs.cover_available.source,
                )
            if not inputs.cover_ready.usable or not inputs.cover_ready.value:
                return SafetyDecision(
                    status="blocked",
                    reason="cover_apply_readiness_not_fresh_and_positive",
                    approved_target=None,
                    opening_state=opening.value,
                    source=inputs.cover_ready.source,
                )
            return SafetyDecision(
                status="safe_position",
                reason="fully_open_window_requires_configured_safety_position",
                approved_target=self.config.target("window_safety"),
                opening_state=opening.value,
                source=inputs.opening_state.source,
            )
        if opening is OpeningState.TILTED:
            if not inputs.opening_safe_for_blind.usable or not inputs.opening_safe_for_blind.value:
                return SafetyDecision(
                    status="blocked",
                    reason="tilted_window_not_explicitly_safe_for_blind",
                    approved_target=None,
                    opening_state=opening.value,
                    source=_source(inputs.opening_state, inputs.opening_safe_for_blind),
                )
        elif opening is not OpeningState.CLOSED:
            return SafetyDecision(
                status="blocked",
                reason="opening_state_unknown_rejects_apply",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.opening_state.source,
            )
        if fachlicher_target is None:
            return SafetyDecision(
                status="blocked",
                reason="no_positive_open_or_protection_target",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.opening_state.source,
            )
        if not inputs.cover_available.usable or not inputs.cover_available.value:
            return SafetyDecision(
                status="blocked",
                reason="cover_availability_not_fresh_and_positive",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.cover_available.source,
            )
        if not inputs.cover_ready.usable or not inputs.cover_ready.value:
            return SafetyDecision(
                status="blocked",
                reason="cover_apply_readiness_not_fresh_and_positive",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.cover_ready.source,
            )
        return SafetyDecision(
            status="ready",
            reason="opening_and_cover_readiness_positive",
            approved_target=fachlicher_target,
            opening_state=opening.value,
            source=_source(inputs.opening_state, inputs.cover_available, inputs.cover_ready),
        )

    def _apply(
        self,
        *,
        effective_target: float | None,
        safety: SafetyDecision,
        override: ManualOverride,
        cooldown: CooldownTracker | None,
        now: float,
    ) -> ApplyDecision:
        if safety.status == "blocked":
            return ApplyDecision(
                status="blocked",
                reason=safety.reason,
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
            )
        if not self.config.automation_enabled:
            return ApplyDecision(
                status="blocked",
                reason="automation_disabled",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
            )
        if not self.config.apply_enabled:
            return ApplyDecision(
                status="blocked",
                reason="apply_disabled",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
            )
        if safety.status == "safe_position":
            return ApplyDecision(
                status="safety_ready",
                reason="safety_target_bypasses_normal_cooldown",
                requested_target=effective_target,
                approved_target=effective_target,
                cooldown_pending_target=None,
            )
        pending = None
        status = "shadow_ready"
        reason = "shadow_intent_only_no_write_path"
        if cooldown is not None and effective_target is not None:
            proposed = cooldown.propose(
                effective_target,
                now=now,
                cooldown_seconds=self.config.apply_cooldown_seconds,
            )
            if not proposed.apply_now:
                status = "cooldown"
                reason = proposed.reason
                pending = proposed.pending_target
        return ApplyDecision(
            status=status,
            reason=reason,
            requested_target=effective_target,
            approved_target=effective_target,
            cooldown_pending_target=pending,
        )

    def _failure(
        self,
        inputs: BlindControlInputs,
        failure_hold_target: float | None,
    ) -> FailureDecision:
        """Block automatic decisions until all closing-demand inputs are proven.

        The gate deliberately runs even when the candidate composition already
        yielded a target.  Otherwise a default daytime target could turn missing
        temperature, activity, or solar evidence into a new opening movement.
        A fully known neutral situation reaches this method with no blockers and
        therefore remains ``normal``.
        """

        quality_blockers = _automatic_decision_quality_blockers(inputs)
        if quality_blockers:
            hold_target = _valid_hold_target(failure_hold_target)
            return FailureDecision(
                status="holding_safe_position" if hold_target is not None else "apply_blocked",
                reason="automatic_decision_quality_gate_blocked",
                hold_target=hold_target,
                quality_blockers=quality_blockers,
            )
        return FailureDecision()

    def _master_mode(
        self,
        *,
        override: ManualOverride,
        waking: bool,
        failure: FailureDecision,
    ) -> MasterMode:
        """Keep operating mode independent from Safety, Apply and winner category."""

        if override.active and override.observed_position is not None and not waking:
            return MasterMode.MANUAL
        if failure.active:
            return MasterMode.FAILURE
        return MasterMode.NORMAL

    def _winner(
        self,
        candidates: list[Candidate],
        winner_keys: tuple[str, ...],
        fachlicher_target: float | None,
    ) -> DecisionWinner | None:
        """Choose the first deterministic winner while retaining all tie keys."""

        if fachlicher_target is None:
            for candidate in candidates:
                if candidate.key == "neutral_context" and candidate.active and not candidate.paused:
                    return DecisionWinner(
                        category=candidate.category,
                        variant=candidate.variant,
                        candidate_key=candidate.key,
                        target_position=None,
                    )
            return None
        winner_set = set(winner_keys)
        for candidate in candidates:
            if candidate.key in winner_set:
                return DecisionWinner(
                    category=candidate.category,
                    variant=candidate.variant,
                    candidate_key=candidate.key,
                    target_position=candidate.target_position,
                )
        return None

    def _failure_apply(
        self, failure: FailureDecision, effective_target: float | None
    ) -> ApplyDecision:
        """Block automatic apply during failure even when a hold target is known."""

        return ApplyDecision(
            status="blocked",
            reason=failure.reason or "decision_failure",
            requested_target=effective_target,
            approved_target=None,
            cooldown_pending_target=None,
        )

    def _active_mode(self, candidates: list[Candidate], *, waking: bool) -> str:
        if waking:
            return "waking"
        for key in ("sleep", "away", "private_time", "privacy", "manual_override"):
            if any(
                candidate.key == key and candidate.active and not candidate.paused
                for candidate in candidates
            ):
                return key
        return (
            "daylight"
            if any(
                candidate.key == "base_daylight" and candidate.active for candidate in candidates
            )
            else "none"
        )

    def _reasons(
        self,
        candidates: list[Candidate],
        paused: list[PausedRequirement],
        fachlicher_target: float | None,
        failure: FailureDecision,
        safety: SafetyDecision,
        apply: ApplyDecision,
    ) -> tuple[str, ...]:
        reasons = [candidate.reason for candidate in candidates if candidate.active]
        reasons.extend(item.reason for item in paused)
        if fachlicher_target is None:
            reasons.append("no_positive_open_reason_no_100_percent_fallback")
        if failure.reason:
            reasons.append(failure.reason)
        reasons.append(safety.reason)
        reasons.append(apply.reason)
        return tuple(dict.fromkeys(reasons))

    def _candidate(
        self,
        key: str,
        category: str,
        active: bool,
        target: float | None,
        source: str,
        reason: str,
        quality: InputQuality,
        *,
        variant: str | None = None,
        paused: bool = False,
        suppressed_by: str | None = None,
    ) -> Candidate:
        return Candidate(
            key=key,
            category=category,
            variant=variant,
            active=active,
            target_position=target,
            source=source,
            reason=reason,
            quality=quality,
            paused=paused,
            suppressed_by=suppressed_by,
        )


def _is_value(observation: InputObservation, expected: str) -> bool:
    return observation.usable and str(observation.value).lower() == expected


def _activity(inputs: BlindControlInputs, values: frozenset[str]) -> bool:
    return inputs.activity_state.usable and str(inputs.activity_state.value).lower() in values


def _opening(observation: InputObservation[str]) -> OpeningState:
    if not observation.usable:
        return OpeningState.UNKNOWN
    try:
        return OpeningState(str(observation.value).lower())
    except ValueError:
        return OpeningState.UNKNOWN


def _quality(*observations: InputObservation) -> InputQuality:
    for observation in observations:
        if not observation.usable:
            return observation.quality
    return InputQuality.FRESH


def _source(*values) -> str:
    sources = [value.source for value in values if hasattr(value, "source")]
    return "+".join(dict.fromkeys(sources)) or "derived"


def _valid_hold_target(value: float | None) -> float | None:
    """Keep failure-hold evidence bounded without inventing a fallback target."""

    if value is None or isinstance(value, bool):
        return None
    try:
        target = float(value)
    except (TypeError, ValueError):
        return None
    return target if 0 <= target <= 100 else None


def _automatic_decision_quality_blockers(
    inputs: BlindControlInputs,
) -> tuple[QualityBlocker, ...]:
    """Return every unresolved input needed to rule out closing demands.

    Core-state mode, thermal load and the complete solar/lux packet jointly
    determine whether Heat, Glare, Cold, Privacy or the daylight opening branch
    may be active.  Any non-fresh observation keeps the result conservative;
    this is intentionally not a target-specific test patch.
    """

    return tuple(
        QualityBlocker(
            key=key,
            quality=observation.quality,
            reason=observation.reason,
        )
        for key in AUTOMATIC_DECISION_QUALITY_INPUTS
        if not (observation := getattr(inputs, key)).usable
    )
