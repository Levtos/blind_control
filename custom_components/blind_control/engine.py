"""Deterministic Blind Control decision tree with separated apply intent."""

from __future__ import annotations

from dataclasses import fields, replace

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
    SafetyDecision,
    SolarExposure,
    SolarExposureState,
)
from .cooldown import CooldownTracker
from .decision import (
    CanonicalFact,
    ContextIntent,
    Contribution,
    DecisionIssue,
    DimensionalDecision,
    SafetyEnvelope,
)
from .environment import EnvironmentalState
from .privacy import with_phase_privacy
from .solar import calculate_solar_exposure

DECISION_CONTRACT_VERSION = "blind_control.decision.v6"
DAYLIGHT_STATES = frozenset({"early_morning", "forenoon", "midday", "afternoon", "late_afternoon"})
TRANSITION_STATES = frozenset({"evening", "late_evening"})
NIGHT_STATES = frozenset({"early_night", "late_night"})
SCREEN_ACTIVITY = frozenset({"screen", "glare", "general_glare"})
TV_ACTIVITY = frozenset({"tv", "console", "streaming", "playstation", "xbox", "switch"})
PC_ACTIVITY = frozenset({"pc", "computer", "workstation"})
EFFECTIVE_SLEEP_STATES = frozenset({"provisional_sleep", "sleep"})
OPENING_CANDIDATES = frozenset({"base_daylight", "storm_approaching", "cool_air_available"})


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
        runtime_ready: bool = True,
        motion_status: str = "idle",
        own_target: float | None = None,
        environment_state: EnvironmentalState | None = None,
    ) -> DecisionTrace:
        inputs = with_phase_privacy(inputs)
        override = override or ManualOverride.inactive()
        solar = calculate_solar_exposure(inputs, self.config)
        candidates: list[Candidate] = []
        paused: list[PausedRequirement] = []

        waking = _is_value(inputs.bio_state, "waking")
        candidates.append(self._base_candidate(inputs))
        candidates.extend(self._mode_candidates(inputs, waking=waking, override=override))

        environment = self._environment_candidates(inputs, solar, environment_state, now or 0.0)
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
        decision = self._dimensional(inputs, solar, candidates, waking=waking, override=override)
        fachlicher_target = decision.target_position
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
        # Compatibility projection: comfort issues no longer turn the entire
        # automatic decision into a failure. Directional fallback lives above.
        failure = FailureDecision()
        master_mode = self._master_mode(override=override, waking=waking, failure=failure)
        safety = self._safety(inputs, fachlicher_target)
        envelope = SafetyEnvelope(
            min_open=safety.approved_target if safety.status == "safe_position" else 0.0,
            block_direction="both" if safety.status == "blocked" else None,
            status=safety.status,
            reason=safety.reason,
        )
        decision = replace(decision, safety=envelope).arbitrate(
            control_hold=override.observed_position if override.active and not waking else None
        )
        effective_target = decision.target_position if safety.status != "blocked" else None
        if safety.status == "safe_position":
            safety = replace(safety, approved_target=effective_target)
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
                runtime_ready=runtime_ready,
                current_position=float(inputs.cover_position.value)
                if inputs.cover_position.usable
                else None,
                motion_status=motion_status,
                own_target=own_target,
                closing=inputs.cover_motion.usable and inputs.cover_motion.value == "closing",
            )
        )
        # Do not open before an entering protection has finished its dwell.
        if (
            safety.status == "ready"
            and apply.status in {"live_ready", "shadow_ready"}
            and inputs.cover_position.usable
            and effective_target is not None
            and effective_target >= float(inputs.cover_position.value)
            and any(
                item.reason == "quality_loss_blocks_only_opening" for item in decision.contributions
            )
        ):
            apply = replace(
                apply,
                status="blocked",
                reason="feature_opening_direction_blocked",
                approved_target=None,
                write_path_reachable=False,
            )
        # Hard modes and technical gates are evaluated independently above.
        if (
            environment_state is not None
            and not waking
            and winner is not None
            and winner.candidate_key
            in OPENING_CANDIDATES
            | {"heat_protection", "glare_general", "glare_tv", "glare_pc", "cold_insulation"}
            and safety.status == "ready"
            and not failure.active
            and apply.status in {"live_ready", "shadow_ready"}
            and effective_target is not None
        ):
            pending_targets = []
            for state, profile in (
                (environment_state.heat, "heat_protection"),
                (environment_state.cold, "cold_insulation"),
            ):
                if state.pending is True:
                    pending_targets.append(self.config.target(profile))
            if environment_state.glare.pending is True:
                for activities, profile in (
                    (SCREEN_ACTIVITY, "glare_general"),
                    (TV_ACTIVITY, "glare_tv"),
                    (PC_ACTIVITY, "glare_pc"),
                ):
                    if _activity(inputs, activities):
                        pending_targets.append(self.config.target(profile))
            if pending_targets and effective_target > min(pending_targets):
                apply = replace(
                    apply,
                    status="blocked",
                    reason="environment_protection_stabilizing",
                    approved_target=None,
                    write_path_reachable=False,
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
            decision=replace(decision, target_position=effective_target, apply_status=apply.status),
        )

    def _dimensional(
        self,
        inputs: BlindControlInputs,
        solar: SolarExposure,
        candidates: list[Candidate],
        *,
        waking: bool,
        override: ManualOverride,
    ) -> DimensionalDecision:
        """Compose independent contexts, restrictions and positive opening evidence."""
        active = {item.key: item for item in candidates if item.active and not item.paused}
        context = ContextIntent()
        for key in ("waking", "sleep", "away", "base_daylight"):
            if key in active:
                item = active[key]
                context = ContextIntent(
                    mode="daylight" if key == "base_daylight" else key,
                    variant=str(inputs.bio_state.value) if key == "sleep" else None,
                    base_target=item.target_position,
                )
                break
        issues: list[DecisionIssue] = []
        contributions: list[Contribution] = []
        dependencies = {
            "glare": ("activity_state",),
            "heat": ("indoor_temperature", "outdoor_temperature"),
            "cold": ("outdoor_temperature", "outdoor_lux"),
            "privacy": ("privacy",),
            "private_time": ("private_time",),
            "context": ("bio_state", "away"),
        }
        for feature, keys in dependencies.items():
            if waking and feature in {"glare", "heat", "cold", "privacy", "context"}:
                continue
            for key in keys:
                observation = getattr(inputs, key)
                if not observation.usable:
                    issues.append(
                        DecisionIssue(
                            feature,
                            key,
                            observation.quality.value,
                            observation.owner,
                            observation.timestamp_basis,
                            observation.reason,
                            fallback="block_opening_direction",
                        )
                    )
        if solar.state == SolarExposureState.UNKNOWN and not waking:
            for feature in ("glare", "heat"):
                for blocker in solar.quality_blockers:
                    observation = getattr(inputs, blocker.key)
                    issues.append(
                        DecisionIssue(
                            feature,
                            blocker.key,
                            blocker.quality.value,
                            observation.owner,
                            observation.timestamp_basis,
                            blocker.reason,
                            "block_opening_direction",
                        )
                    )
        if context.mode == "daylight" and solar.lifecycle != "ACTIVE":
            context = replace(context, base_target=None)
            issues.append(
                DecisionIssue(
                    "daylight",
                    "sun_horizon",
                    "unknown" if solar.lifecycle == "UNKNOWN" else "conflict",
                    "ha_sun",
                    "stateful_truth",
                    "day_solar_consistency",
                    "no_daylight_open",
                )
            )
        for feature, keys in (
            ("storm", ("weather_alert", "precipitation_trend", "wind_trend", "pressure_trend")),
            ("cool_air", ("air_movement", "indoor_temperature", "outdoor_temperature")),
            ("daylight", ("day_state", "day_context")),
            (
                "solar_diagnostic",
                (
                    "sun_azimuth",
                    "outdoor_lux",
                    "lux_trend",
                    "expected_direct_radiation",
                    "expected_diffuse_radiation",
                    "cloud_cover",
                ),
            ),
        ):
            for key in keys:
                observation = getattr(inputs, key)
                if not observation.usable:
                    issues.append(
                        DecisionIssue(
                            feature,
                            key,
                            observation.quality.value,
                            observation.owner,
                            observation.timestamp_basis,
                            observation.reason,
                            fallback="no_positive_evidence",
                            severity="diagnostic_warning",
                        )
                    )
        for item in candidates:
            if item.key in {
                "sleep",
                "away",
                "waking",
                "base_daylight",
                "neutral_context",
                "manual_override",
            }:
                continue
            feature = {
                "heat_protection": "heat",
                "cold_insulation": "cold",
                "storm_approaching": "storm",
                "cool_air_available": "cool_air",
            }.get(item.key, item.category)
            if item.key == "private_time":
                feature = "private_time"
            contributions.append(
                Contribution(
                    feature,
                    item.variant,
                    "open_reason" if item.key in OPENING_CANDIDATES else "max_open",
                    item.target_position,
                    "paused" if item.paused else "active" if item.active else "inactive",
                    item.reason,
                )
            )
        # No stale command is retained. A quality-loss guard uses the CURRENT
        # position and permits every stronger independent closing requirement.
        # Waking explicitly pauses comfort scopes; private_time remains separate.
        if issues and not (override.active and not waking):
            for feature in sorted(
                {item.feature for item in issues if item.fallback == "block_opening_direction"}
            ):
                contributions.append(
                    Contribution(
                        feature,
                        None,
                        "max_open",
                        float(inputs.cover_position.value) if inputs.cover_position.usable else 0.0,
                        "active",
                        "quality_loss_blocks_only_opening",
                    )
                )
        evidence = tuple(
            CanonicalFact(
                field.name,
                observation.value,
                observation.quality.value,
                observation.owner,
                observation.timestamp_basis,
                observation.updated_at.isoformat() if observation.updated_at else None,
                observation.source_revision,
                observation.reason,
                observation.evidence,
            )
            for field in fields(inputs)
            for observation in (getattr(inputs, field.name),)
        )
        return DimensionalDecision(
            context, tuple(contributions), tuple(issues), evidence
        ).arbitrate(
            control_hold=override.observed_position if override.active and not waking else None
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
        effective_sleep = _is_any_value(inputs.bio_state, EFFECTIVE_SLEEP_STATES)
        candidates = [
            self._candidate(
                "sleep",
                "sleep",
                effective_sleep,
                self.config.target("sleep") if effective_sleep else None,
                inputs.bio_state.source,
                "canonical_bio_state_effective_sleep"
                if effective_sleep
                else "bio_state_not_effective_sleep",
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
        state: EnvironmentalState | None = None,
        now: float = 0.0,
    ) -> list[Candidate]:
        storm = self._storm_active(inputs)
        heat, heat_reason = self._heat_active(
            inputs, solar, storm, held=bool(state and state.heat.active)
        )
        glare_relevant = self._glare_relevant(solar, held=bool(state and state.glare.active))
        cold = self._cold_active(inputs, solar, held=bool(state and state.cold.active))
        if state is not None:
            solar_valid = not solar.quality_blockers and solar.state != SolarExposureState.UNKNOWN
            for transition, desired, valid in (
                (
                    state.heat,
                    heat,
                    solar_valid
                    and inputs.indoor_temperature.usable
                    and inputs.outdoor_temperature.usable,
                ),
                (state.glare, glare_relevant, solar_valid),
                (state.cold, cold, inputs.outdoor_lux.usable and inputs.outdoor_temperature.usable),
            ):
                transition.observe(
                    desired,
                    now=now,
                    enter=self.config.environment_enter_seconds,
                    exit=self.config.environment_exit_seconds,
                    valid=valid,
                )
            heat = (
                state.heat.active
                and solar_valid
                and inputs.indoor_temperature.usable
                and inputs.outdoor_temperature.usable
            )
            glare_relevant = state.glare.active and solar_valid
            cold = (
                state.cold.active
                and inputs.outdoor_lux.usable
                and inputs.outdoor_temperature.usable
            )
            if state.heat.pending is not None:
                heat_reason = (
                    "environment_enter_pending"
                    if state.heat.pending
                    else "environment_exit_pending"
                )
        glare_general = glare_relevant and _activity(inputs, SCREEN_ACTIVITY)
        glare_tv = glare_relevant and _activity(inputs, TV_ACTIVITY)
        glare_pc = glare_relevant and _activity(inputs, PC_ACTIVITY)
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

    def _glare_relevant(self, solar: SolarExposure, *, held: bool = False) -> bool:
        """Use an independent window-solar signal for screen glare."""

        return (
            solar.state
            in {
                SolarExposureState.DIRECT_SUN,
                SolarExposureState.CLOUD_SHADOW,
                SolarExposureState.DIFFUSE_BRIGHT,
            }
            or self._within_solar_hold_band(solar, held)
        ) and solar.confidence >= self.config.glare_confidence_threshold * (
            self.config.environment_hysteresis_ratio if held else 1.0
        )

    def _within_solar_hold_band(self, solar: SolarExposure, held: bool) -> bool:
        return (
            held
            and solar.state == SolarExposureState.SOLAR_NOT_ON_WINDOW
            and solar.incidence_factor is not None
            and solar.incidence_factor
            >= self.config.minimum_incidence_factor * self.config.environment_hysteresis_ratio
        )

    def _heat_active(
        self,
        inputs: BlindControlInputs,
        solar: SolarExposure,
        storm: bool,
        *,
        held: bool = False,
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
        } or self._within_solar_hold_band(solar, held)
        if storm:
            return False, "storm_approaching_relaxes_heat"
        if (
            thermal_load
            and solar_possible
            and solar.confidence
            >= self.config.heat_confidence_threshold
            * (self.config.environment_hysteresis_ratio if held else 1.0)
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

    def _cold_active(
        self, inputs: BlindControlInputs, solar: SolarExposure, *, held: bool = False
    ) -> bool:
        return (
            inputs.outdoor_temperature.usable
            and float(inputs.outdoor_temperature.value) <= self.config.cold_outdoor_threshold
            and inputs.outdoor_lux.usable
            and (
                float(inputs.outdoor_lux.value) <= self.config.cold_lux_exit_threshold
                if held
                else float(inputs.outdoor_lux.value) < self.config.cold_lux_enter_threshold
            )
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
        if not inputs.cover_position.usable:
            return SafetyDecision(
                status="blocked",
                reason="cover_position_evidence_not_fresh",
                approved_target=None,
                opening_state=opening.value,
                source=inputs.cover_position.source,
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
                approved_target=max(
                    self.config.target("window_safety"), float(inputs.cover_position.value)
                ),
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
        runtime_ready: bool,
        current_position: float | None,
        motion_status: str,
        own_target: float | None,
        closing: bool,
    ) -> ApplyDecision:
        decision_context = {
            "runtime_mode": self.config.runtime_mode,
            "apply_owner": self.config.apply_owner,
        }
        if safety.status == "blocked":
            return ApplyDecision(
                status="blocked",
                reason=safety.reason,
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if not self.config.automation_enabled:
            return ApplyDecision(
                status="blocked",
                reason="automation_disabled",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if not self.config.apply_enabled:
            return ApplyDecision(
                status="blocked",
                reason="apply_disabled",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if override.active and safety.status != "safe_position":
            return ApplyDecision(
                status="manual_hold",
                reason="manual_override_blocks_automatic_apply",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if not runtime_ready and safety.status != "safe_position":
            return ApplyDecision(
                status="blocked",
                reason="restart_baseline_pending",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if self.config.runtime_mode == "live" and self.config.apply_owner != "blind_control":
            return ApplyDecision(
                status="blocked",
                reason="exclusive_apply_owner_not_confirmed",
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        if effective_target is None:
            return ApplyDecision(
                status="idle",
                reason="no_effective_target",
                requested_target=None,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        pending = None
        safety_drive = safety.status == "safe_position"
        if motion_status != "idle" and not (
            safety_drive
            and (
                closing
                or own_target != effective_target
                or motion_status in {"target_not_reached", "command_error"}
            )
        ):
            return ApplyDecision(
                status="blocked",
                reason=motion_status,
                requested_target=effective_target,
                approved_target=None,
                cooldown_pending_target=None,
                **decision_context,
            )
        ready = True
        reason = "target_ready"
        if cooldown is not None and effective_target is not None:
            proposed = cooldown.propose(
                effective_target,
                now=now,
                cooldown_seconds=self.config.apply_cooldown_seconds,
                bypass_cooldown=safety.status == "safe_position",
                current_position=None if safety_drive and closing else current_position,
            )
            if not proposed.apply_now:
                status = "stable" if proposed.reason == "identical_target" else "cooldown"
                reason = proposed.reason
                pending = proposed.pending_target
                ready = False
                return ApplyDecision(
                    status=status,
                    reason=reason,
                    requested_target=effective_target,
                    approved_target=None,
                    cooldown_pending_target=pending,
                    **decision_context,
                )
            reason = proposed.reason
        if safety.status == "safe_position":
            status = "safety_ready"
            reason = "safety_target_bypasses_normal_cooldown"
        elif self.config.runtime_mode == "shadow":
            status = "shadow_ready"
            reason = "shadow_intent_only_no_write_path"
        else:
            status = "live_ready"
        return ApplyDecision(
            status=status,
            reason=reason,
            requested_target=effective_target,
            approved_target=effective_target if ready else None,
            cooldown_pending_target=pending,
            write_path_reachable=(
                self.config.runtime_mode == "live"
                and self.config.apply_owner == "blind_control"
                and self.config.apply_enabled
            ),
            **decision_context,
        )

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
            runtime_mode=self.config.runtime_mode,
            apply_owner=self.config.apply_owner,
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


def _is_any_value(observation: InputObservation, expected: frozenset[str]) -> bool:
    return observation.usable and str(observation.value).lower() in expected


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
