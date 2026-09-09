from __future__ import annotations

import sys
import types
import unittest
from dataclasses import replace
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "blind_control"
if "custom_components.blind_control" not in sys.modules:
    package = types.ModuleType("custom_components.blind_control")
    package.__path__ = [str(PACKAGE)]
    sys.modules["custom_components.blind_control"] = package

# The package initializer imports Home Assistant; pure engine tests install a
# namespace package so they can exercise the HA-independent modules directly.
from custom_components.blind_control.config import BlindControlConfig  # noqa: E402
from custom_components.blind_control.contracts import (  # noqa: E402
    BlindControlInputs,
    InputObservation,
    InputQuality,
    SolarExposureState,
)
from custom_components.blind_control.cooldown import CooldownTracker  # noqa: E402
from custom_components.blind_control.engine import DecisionEngine  # noqa: E402
from custom_components.blind_control.open_meteo import suggested_open_meteo_url  # noqa: E402
from custom_components.blind_control.shadow import ShadowRuntime  # noqa: E402
from custom_components.blind_control.shadow_diff import DiffClassification  # noqa: E402
from custom_components.blind_control.solar import calculate_solar_exposure  # noqa: E402
from custom_components.blind_control.ux_contract import (  # noqa: E402
    UX_CONTRACT_VERSION,
    build_ux_snapshot,
)


def fresh(value, source: str):
    return InputObservation(value=value, source=source, quality=InputQuality.FRESH)


def stale(value, source: str):
    return InputObservation(value=value, source=source, quality=InputQuality.STALE)


def ready_inputs() -> BlindControlInputs:
    return BlindControlInputs(
        bio_state=fresh("awake", "core_state.bio"),
        activity_state=fresh("none", "core_state.activity"),
        day_state=fresh("forenoon", "core_state.day"),
        day_context=fresh("weekday", "core_state.context"),
        away=fresh(False, "core_state.away"),
        private_time=fresh(False, "core_state.private"),
        privacy=fresh(False, "core_state.privacy"),
        opening_state=fresh("closed", "opening_contract"),
        opening_safe_for_blind=fresh(True, "opening_contract"),
        cover_available=fresh(True, "technical_cover"),
        cover_ready=fresh(True, "technical_readiness"),
        cover_position=fresh(50.0, "technical_cover"),
        outdoor_lux=fresh(14_000.0, "lux_sensor"),
        lux_trend=fresh(0.0, "lux_sensor"),
        sun_elevation=fresh(30.0, "sun_contract"),
        sun_azimuth=fresh(304.0, "sun_contract"),
        expected_direct_radiation=fresh(400.0, "weather_model"),
        expected_diffuse_radiation=fresh(50.0, "weather_model"),
        cloud_cover=fresh(0.1, "weather_model"),
        indoor_temperature=fresh(22.0, "room_temperature"),
        outdoor_temperature=fresh(20.0, "weather_temperature"),
    )


def sunny_inputs(**changes) -> BlindControlInputs:
    values = {
        "sun_elevation": fresh(30.0, "sun_contract"),
        "sun_azimuth": fresh(124.0, "sun_contract"),
        "outdoor_lux": fresh(14_000.0, "lux_sensor"),
        "lux_trend": fresh(0.0, "lux_sensor"),
        "expected_direct_radiation": fresh(400.0, "weather_model"),
        "expected_diffuse_radiation": fresh(50.0, "weather_model"),
        "cloud_cover": fresh(0.1, "weather_model"),
    }
    values.update(changes)
    return replace(ready_inputs(), **values)


class DecisionEngineTests(unittest.TestCase):
    def test_vertical_slice_produces_trace_and_non_actuating_snapshot(self) -> None:
        runtime = ShadowRuntime()
        snapshot = runtime.evaluate(ready_inputs(), evaluated_at=None, now=0)

        self.assertEqual(snapshot.version, "blind_control.runtime.v4")
        self.assertTrue(snapshot.shadow_only)
        self.assertFalse(snapshot.actuation_executed)
        self.assertFalse(snapshot.write_path_reachable)
        self.assertIsInstance(snapshot.as_dict()["trace"], dict)
        projection = build_ux_snapshot(snapshot, BlindControlConfig.defaults())
        self.assertEqual(projection["version"], UX_CONTRACT_VERSION)
        self.assertEqual(projection["overview"]["master_mode"], "normal")
        self.assertEqual(projection["overview"]["winner"]["category"], "neutral")
        self.assertEqual(projection["overview"]["cover_position"], 50.0)
        self.assertFalse(projection["overview"]["household"]["away"])
        self.assertIn("cover_position", projection["settings"]["binding_freshness"])
        self.assertEqual(
            projection["automation_projection"]["version"],
            "blind_control.automation_projection.v5",
        )
        self.assertIn("binding_groups", projection["settings"])
        core_group = next(
            group
            for group in projection["settings"]["binding_groups"]
            if group["key"] == "core_state_bindings"
        )
        self.assertEqual(core_group["readiness"], "missing_required")
        self.assertIn("bio_state", core_group["missing_required"])
        self.assertEqual(
            next(field for field in core_group["fields"] if field["key"] == "bio_state")[
                "requirement"
            ],
            "required",
        )

    def test_ux_distinguishes_internal_provider_external_override_and_unavailable(self) -> None:
        snapshot = ShadowRuntime().evaluate(ready_inputs(), now=0)
        configured = BlindControlConfig.from_mapping(
            {"open_meteo_api_url": suggested_open_meteo_url(50, 8)}
        )

        def radiation_status(projection, key):
            solar = next(
                group
                for group in projection["settings"]["binding_groups"]
                if group["key"] == "solar_bindings"
            )
            return next(field for field in solar["fields"] if field["key"] == key)["status"]

        ready = build_ux_snapshot(snapshot, configured, provider_status="ready")
        self.assertEqual(
            radiation_status(ready, "expected_direct_radiation"),
            "internal_provider_active",
        )
        unavailable = build_ux_snapshot(snapshot, configured, provider_status="unavailable")
        self.assertEqual(
            radiation_status(unavailable, "expected_direct_radiation"),
            "provider_unavailable",
        )
        external = BlindControlConfig.from_mapping(
            {
                **configured.to_mapping(),
                "input_bindings": {"expected_direct_radiation": "sensor.external_contract"},
            }
        )
        projected = build_ux_snapshot(snapshot, external, provider_status="unavailable")
        self.assertEqual(
            radiation_status(projected, "expected_direct_radiation"),
            "external_override_active",
        )

    def test_missing_inputs_never_fall_silently_to_open(self) -> None:
        trace = DecisionEngine().evaluate(BlindControlInputs.empty())

        self.assertIsNone(trace.fachlicher_target)
        self.assertIsNone(trace.effective_target)
        self.assertEqual(trace.master_mode.value, "normal")
        self.assertTrue(trace.decision.issues)
        self.assertEqual(trace.safety.status, "blocked")
        self.assertIn("no_positive_open_reason_no_100_percent_fallback", trace.reasons)
        self.assertFalse(trace.apply.write_path_reachable)

    def test_automatic_quality_gate_matrix_blocks_uncertain_daylight_opening(self) -> None:
        """A target may exist, but unresolved protection evidence must still hold."""

        complete = replace(ready_inputs(), cover_position=fresh(42.0, "technical_cover"))
        fields = {
            "indoor_temperature": 22.0,
            "outdoor_temperature": 20.0,
            "activity_state": "none",
            "outdoor_lux": 14_000.0,
            "sun_elevation": 30.0,
            "sun_azimuth": 304.0,
        }
        quality_cases = {
            "valid": InputQuality.FRESH,
            "missing": None,
            "unknown": InputQuality.UNKNOWN,
            "unavailable": InputQuality.UNAVAILABLE,
            "stale": InputQuality.STALE,
            "conflict": InputQuality.CONFLICT,
        }

        for key, value in fields.items():
            for case, quality in quality_cases.items():
                with self.subTest(field=key, quality=case):
                    observation = (
                        fresh(value, f"owner.{key}")
                        if quality is InputQuality.FRESH
                        else InputObservation.missing(f"owner.{key}", reason="matrix_missing")
                        if quality is None
                        else InputObservation(
                            value=value,
                            source=f"owner.{key}",
                            quality=quality,
                            reason=f"matrix_{case}",
                        )
                    )
                    runtime = ShadowRuntime()
                    runtime.evaluate(complete, now=0)
                    trace = runtime.evaluate(replace(complete, **{key: observation}), now=1).trace

                    if case == "valid":
                        self.assertEqual(trace.master_mode.value, "normal")
                        self.assertEqual(trace.failure.status, "none")
                        self.assertEqual(trace.effective_target, 100)
                        continue

                    self.assertIn(trace.fachlicher_target, (None, 42))
                    self.assertEqual(trace.master_mode.value, "normal")
                    self.assertFalse(trace.failure.active)
                    self.assertIn(trace.effective_target, (None, 42))
                    self.assertEqual(
                        trace.apply.status, "idle" if trace.effective_target is None else "stable"
                    )
                    self.assertFalse(trace.apply.write_path_reachable)
                    self.assertNotEqual(trace.effective_target, 100)
                    blocker = next(item for item in trace.decision.issues if item.evidence == key)
                    self.assertEqual(
                        blocker.reason, "matrix_missing" if case == "missing" else f"matrix_{case}"
                    )

    def test_replaceable_solar_evidence_quality_does_not_block_valid_combination(self) -> None:
        complete = replace(ready_inputs(), cover_position=fresh(42.0, "technical_cover"))
        optional_fields = {
            "lux_trend": 0.0,
            "expected_direct_radiation": 400.0,
            "expected_diffuse_radiation": 50.0,
            "cloud_cover": 0.1,
        }
        unresolved_qualities = (
            InputQuality.UNKNOWN,
            InputQuality.UNAVAILABLE,
            InputQuality.STALE,
            InputQuality.CONFLICT,
        )

        for key, value in optional_fields.items():
            for quality in unresolved_qualities:
                with self.subTest(field=key, quality=quality):
                    observation = InputObservation(
                        value=value,
                        source=f"owner.{key}",
                        quality=quality,
                        reason=f"replaceable_{quality.value}",
                    )
                    trace = DecisionEngine().evaluate(replace(complete, **{key: observation}))

                    self.assertEqual(trace.master_mode.value, "normal")
                    self.assertEqual(trace.failure.status, "none")
                    self.assertEqual(trace.effective_target, 100)
                    self.assertNotIn(
                        key,
                        {blocker.key for blocker in trace.failure.quality_blockers},
                    )

    def test_capability_aware_solar_evidence_combinations(self) -> None:
        missing = InputObservation.missing(reason="owner_binding_not_configured")
        base = replace(
            ready_inputs(),
            cover_position=fresh(42.0, "technical_cover"),
            lux_trend=missing,
            expected_direct_radiation=missing,
            expected_diffuse_radiation=missing,
            cloud_cover=missing,
        )

        lux_geometry = DecisionEngine().evaluate(base)
        derived_trend = DecisionEngine().evaluate(
            replace(
                base,
                lux_trend=InputObservation(
                    value=-250.0,
                    source="owner.lux",
                    quality=InputQuality.FRESH,
                    reason="derived_from_consecutive_fresh_lux_observations",
                ),
            )
        )
        model_without_trend = DecisionEngine().evaluate(
            replace(
                base,
                expected_direct_radiation=fresh(400.0, "owner.model"),
                expected_diffuse_radiation=fresh(50.0, "owner.model"),
            )
        )
        insufficient = DecisionEngine().evaluate(
            replace(base, outdoor_lux=InputObservation.missing(reason="matrix_missing")),
            failure_hold_target=42.0,
        )

        for trace in (lux_geometry, derived_trend, model_without_trend):
            self.assertEqual(trace.master_mode.value, "normal")
            self.assertEqual(trace.failure.status, "none")
            self.assertEqual(trace.effective_target, 100)
        self.assertIn("lux_trend", derived_trend.solar.derived_evidence)
        self.assertIn("expected_direct_radiation", model_without_trend.solar.used_evidence)
        self.assertIn("lux_trend", lux_geometry.solar.missing_optional_capabilities)
        self.assertEqual(insufficient.master_mode.value, "normal")
        self.assertEqual(insufficient.effective_target, 42.0)
        self.assertEqual(insufficient.apply.status, "blocked")
        self.assertNotEqual(insufficient.effective_target, 100)

    def test_canonical_day_phases_have_explicit_daylight_transition_and_night_semantics(
        self,
    ) -> None:
        daylight = {
            "early_morning",
            "forenoon",
            "midday",
            "afternoon",
            "late_afternoon",
        }
        transition = {"evening", "late_evening"}
        night = {"early_night", "late_night"}

        for phase in daylight | transition | night:
            with self.subTest(phase=phase):
                trace = DecisionEngine().evaluate(
                    replace(ready_inputs(), day_state=fresh(phase, "core_state.day"))
                )
                self.assertEqual(trace.master_mode.value, "normal")
                if phase in daylight:
                    self.assertEqual(trace.fachlicher_target, 100)
                    self.assertIn("base_daylight", trace.winner_keys)
                else:
                    self.assertEqual(trace.fachlicher_target, 40)
                    self.assertEqual(trace.winner.category, "privacy")

    def test_daylight_phase_conflicting_with_sun_below_horizon_blocks_opening(self) -> None:
        inputs = replace(
            ready_inputs(),
            cover_position=fresh(42.0, "technical_cover"),
            sun_elevation=fresh(-2.0, "sun_contract"),
        )
        trace = DecisionEngine().evaluate(inputs, failure_hold_target=42.0)

        self.assertIsNone(trace.fachlicher_target)
        self.assertEqual(trace.master_mode.value, "normal")
        self.assertIsNone(trace.effective_target)
        self.assertIn(
            "day_solar_consistency",
            {issue.reason for issue in trace.decision.issues},
        )

    def test_missing_cover_position_evidence_blocks_apply_without_inventing_position(self) -> None:
        trace = DecisionEngine().evaluate(
            replace(ready_inputs(), cover_position=InputObservation.missing())
        )

        self.assertEqual(trace.safety.status, "blocked")
        self.assertEqual(trace.safety.reason, "cover_position_evidence_not_fresh")
        self.assertEqual(trace.apply.status, "blocked")
        self.assertIsNone(trace.apply.approved_target)

    def test_cloud_shadow_keeps_heat_active_without_open_fallback(self) -> None:
        inputs = sunny_inputs(
            outdoor_temperature=fresh(34.0, "weather_temperature"),
            lux_trend=fresh(-1_000.0, "lux_sensor"),
            cloud_cover=fresh(0.8, "weather_model"),
            outdoor_lux=fresh(13_000.0, "lux_sensor"),
        )
        trace = DecisionEngine().evaluate(inputs)

        self.assertEqual(trace.solar.state, SolarExposureState.CLOUD_SHADOW)
        self.assertIn("heat_protection", trace.winner_keys)
        self.assertEqual(trace.fachlicher_target, 15)
        self.assertNotEqual(trace.fachlicher_target, 100)

    def test_heat_and_glare_are_independent_pc_glare_survives_heat_end(self) -> None:
        hot = sunny_inputs(
            activity_state=fresh("pc", "core_state.activity"),
            outdoor_temperature=fresh(34.0, "weather_temperature"),
        )
        cool = replace(
            hot,
            outdoor_temperature=fresh(22.0, "weather_temperature"),
            indoor_temperature=fresh(23.0, "room_temperature"),
        )

        hot_trace = DecisionEngine().evaluate(hot)
        cool_trace = DecisionEngine().evaluate(cool)

        self.assertIn("heat_protection", hot_trace.winner_keys)
        self.assertEqual(hot_trace.master_mode.value, "normal")
        self.assertEqual(hot_trace.winner.category, "climate")
        self.assertEqual(hot_trace.winner.variant, "heat")
        glare_pc = next(
            branch for branch in hot_trace.active_branches if branch.candidate_key == "glare_pc"
        )
        self.assertTrue(glare_pc.active)
        self.assertFalse(glare_pc.winner)
        self.assertIn("glare_pc", cool_trace.winner_keys)
        self.assertEqual(cool_trace.winner.category, "glare")
        self.assertEqual(cool_trace.winner.variant, "pc")
        self.assertEqual(cool_trace.fachlicher_target, 75)
        self.assertNotIn("base_daylight", cool_trace.winner_keys)

    def test_normal_hierarchy_projects_glare_pc_and_tv_variants(self) -> None:
        pc_trace = DecisionEngine().evaluate(
            sunny_inputs(activity_state=fresh("pc", "core_state.activity"))
        )
        tv_trace = DecisionEngine().evaluate(
            sunny_inputs(activity_state=fresh("tv", "core_state.activity"))
        )

        self.assertEqual(pc_trace.master_mode.value, "normal")
        self.assertEqual(pc_trace.winner.category, "glare")
        self.assertEqual(pc_trace.winner.variant, "pc")
        self.assertEqual(tv_trace.master_mode.value, "normal")
        self.assertEqual(tv_trace.winner.category, "glare")
        self.assertEqual(tv_trace.winner.variant, "tv")

    def test_manual_override_holds_automation_until_allowed_lifecycle(self) -> None:
        runtime = ShadowRuntime()
        runtime.on_restart(50)
        runtime.observe_cover_position(80, source="foreign_position", now=10)
        runtime.observe_cover_position(80, source="foreign_position", now=12)
        inputs = sunny_inputs(
            activity_state=fresh("pc", "core_state.activity"),
            outdoor_temperature=fresh(34.0, "weather_temperature"),
        )

        runtime.evaluate(inputs, now=10)
        trace = runtime.evaluate(inputs, now=20)

        self.assertEqual(trace.trace.active_mode, "manual_override")
        self.assertEqual(trace.trace.master_mode.value, "manual")
        self.assertEqual(trace.trace.winner.category, "override")
        self.assertIsNone(trace.trace.winner.variant)
        self.assertEqual(trace.trace.fachlicher_target, 80)
        self.assertEqual(trace.trace.effective_target, 80)
        heat = next(item for item in trace.trace.candidates if item.key == "heat_protection")
        self.assertTrue(heat.paused)
        self.assertEqual(heat.suppressed_by, "manual_override")
        self.assertIn("manual_override_holds_automation", trace.trace.reasons)
        self.assertEqual(trace.trace.override.context_key.as_dict()["activity_context"], "pc")

    def test_override_context_lifecycle_is_explicit_and_deterministic(self) -> None:
        runtime = ShadowRuntime()
        runtime.on_restart(50)
        runtime.observe_cover_position(80, source="foreign_position", now=10)
        runtime.observe_cover_position(80, source="foreign_position", now=12)
        tv = replace(ready_inputs(), activity_state=fresh("tv", "core_state.activity"))
        console = replace(tv, activity_state=fresh("console", "core_state.activity"))
        next_day = replace(console, day_state=fresh("night", "core_state.day"))

        first = runtime.evaluate(tv, now=20)
        same_session = runtime.evaluate(console, now=21)
        ended = runtime.evaluate(next_day, now=22)

        self.assertTrue(first.trace.override.active)
        self.assertTrue(same_session.trace.override.active)
        self.assertEqual(first.trace.override.context_key.as_dict()["activity_context"], "screen")
        self.assertFalse(ended.trace.override.active)
        self.assertEqual(ended.trace.override.reason, "override_context_changed")
        self.assertFalse(runtime.observe_cover_position(80, source="same_position", now=23).active)
        self.assertFalse(runtime.observe_cover_position(70, source="new_position", now=24).active)
        self.assertTrue(runtime.observe_cover_position(70, source="new_position", now=26).active)

    def test_apply_disabled_cannot_be_bypassed_by_manual_override(self) -> None:
        config = replace(BlindControlConfig.defaults(), apply_enabled=False)
        runtime = ShadowRuntime(config)
        runtime.on_restart(50)
        runtime.observe_cover_position(80, source="foreign_position", now=10)
        runtime.observe_cover_position(80, source="foreign_position", now=12)

        trace = runtime.evaluate(ready_inputs(), now=20)

        self.assertEqual(trace.trace.fachlicher_target, 80)
        self.assertEqual(trace.trace.apply.status, "blocked")
        self.assertEqual(trace.trace.apply.reason, "apply_disabled")

    def test_waking_pauses_heat_glare_privacy_and_cold_until_awake(self) -> None:
        waking = sunny_inputs(
            bio_state=fresh("waking", "core_state.bio"),
            activity_state=fresh("pc", "core_state.activity"),
            privacy=fresh(True, "core_state.privacy"),
            day_state=fresh("evening", "core_state.day"),
            outdoor_temperature=fresh(34.0, "weather_temperature"),
        )
        awake = replace(waking, bio_state=fresh("awake", "core_state.bio"))

        waking_trace = DecisionEngine().evaluate(waking)
        awake_trace = DecisionEngine().evaluate(awake)

        self.assertEqual(waking_trace.active_mode, "waking")
        self.assertEqual(waking_trace.master_mode.value, "normal")
        self.assertEqual(waking_trace.winner.category, "waking")
        self.assertEqual(waking_trace.fachlicher_target, 100)
        self.assertTrue(
            all(
                candidate.paused
                for candidate in waking_trace.candidates
                if candidate.key in {"heat_protection", "glare_pc", "privacy"} and candidate.active
            )
        )
        paused_branches = {
            branch.candidate_key: branch for branch in waking_trace.active_branches if branch.paused
        }
        self.assertIn("heat_protection", paused_branches)
        self.assertIn("glare_pc", paused_branches)
        self.assertIn("privacy", paused_branches)
        self.assertNotIn("cold_insulation", paused_branches)
        self.assertEqual(awake_trace.fachlicher_target, 15)

    def test_waking_does_not_project_inactive_environment_branches_as_paused(self) -> None:
        trace = DecisionEngine().evaluate(
            replace(ready_inputs(), bio_state=fresh("waking", "core_state.bio"))
        )

        paused = {branch.candidate_key for branch in trace.active_branches if branch.paused}
        self.assertEqual(trace.master_mode.value, "normal")
        self.assertEqual(trace.winner.category, "waking")
        self.assertFalse(
            paused
            & {
                "heat_protection",
                "cold_insulation",
                "glare_general",
                "glare_tv",
                "glare_pc",
            }
        )

    def test_sleep_and_away_are_normal_hierarchy_categories(self) -> None:
        sleeping = DecisionEngine().evaluate(
            replace(ready_inputs(), bio_state=fresh("sleep", "core_state.bio"))
        )
        away = DecisionEngine().evaluate(
            replace(ready_inputs(), away=fresh(True, "core_state.away"))
        )

        self.assertEqual(sleeping.master_mode.value, "normal")
        self.assertEqual(sleeping.winner.category, "sleep")
        self.assertIsNone(sleeping.winner.variant)
        self.assertEqual(away.master_mode.value, "normal")
        self.assertEqual(away.winner.category, "away")
        self.assertIsNone(away.winner.variant)

    def test_provisional_sleep_and_sleep_share_the_configured_sleep_profile(self) -> None:
        self.assertEqual(BlindControlConfig.defaults().target("sleep"), 5)
        config = BlindControlConfig.from_mapping(
            {"profiles": {"sleep": {"normal": 17, "inverted": 83}}}
        )
        engine = DecisionEngine(config)
        provisional = engine.evaluate(
            replace(ready_inputs(), bio_state=fresh("provisional_sleep", "core_state.bio"))
        )
        confirmed = engine.evaluate(
            replace(ready_inputs(), bio_state=fresh("sleep", "core_state.bio"))
        )

        for trace in (provisional, confirmed):
            sleep = next(item for item in trace.candidates if item.key == "sleep")
            self.assertTrue(sleep.active)
            self.assertEqual(sleep.reason, "canonical_bio_state_effective_sleep")
            self.assertEqual(sleep.target_position, engine.config.target("sleep"))
            self.assertEqual(trace.active_mode, "sleep")
            self.assertEqual(trace.winner.category, "sleep")
            self.assertEqual(trace.winner.candidate_key, "sleep")
            self.assertEqual(trace.fachlicher_target, 17)

        self.assertEqual(provisional.fachlicher_target, confirmed.fachlicher_target)

    def test_awake_is_not_effective_sleep(self) -> None:
        trace = DecisionEngine().evaluate(
            replace(ready_inputs(), bio_state=fresh("awake", "core_state.bio"))
        )

        sleep = next(item for item in trace.candidates if item.key == "sleep")
        self.assertFalse(sleep.active)
        self.assertEqual(sleep.reason, "bio_state_not_effective_sleep")
        self.assertNotEqual(trace.active_mode, "sleep")

    def test_waking_clears_a_previous_override_and_pauses_cold_insulation(self) -> None:
        runtime = ShadowRuntime()
        runtime.on_restart(20)
        runtime.observe_cover_position(60, source="foreign_position", now=20)
        cold_waking = replace(
            ready_inputs(),
            bio_state=fresh("waking", "core_state.bio"),
            day_state=fresh("night", "core_state.day"),
            outdoor_temperature=fresh(5.0, "weather_temperature"),
            sun_elevation=fresh(-5.0, "sun_contract"),
            outdoor_lux=fresh(10.0, "lux_sensor"),
            privacy=fresh(True, "core_state.privacy"),
        )

        runtime.evaluate(cold_waking, now=20)
        snapshot = runtime.evaluate(cold_waking, now=30)

        self.assertFalse(snapshot.trace.override.active)
        self.assertEqual(snapshot.trace.fachlicher_target, 100)
        cold = next(item for item in snapshot.trace.candidates if item.key == "cold_insulation")
        self.assertTrue(cold.active)
        self.assertTrue(cold.paused)
        cold_branch = next(
            branch
            for branch in snapshot.trace.active_branches
            if branch.candidate_key == "cold_insulation"
        )
        self.assertTrue(cold_branch.paused)

    def test_waking_uses_only_canonical_bio_state(self) -> None:
        inputs = replace(
            ready_inputs(),
            bio_state=fresh("awake", "core_state.bio"),
            activity_state=fresh("none", "legacy_wake_source"),
        )
        trace = DecisionEngine().evaluate(inputs)

        self.assertNotEqual(trace.active_mode, "waking")
        self.assertFalse(next(item for item in trace.candidates if item.key == "waking").active)

    def test_opening_safety_is_separate_and_blocks_unsafe_tilt(self) -> None:
        inputs = replace(
            ready_inputs(),
            opening_state=fresh("tilted", "opening_contract"),
            opening_safe_for_blind=fresh(False, "opening_contract"),
        )
        trace = DecisionEngine().evaluate(inputs)

        self.assertEqual(trace.safety.status, "blocked")
        self.assertIsNone(trace.effective_target)
        self.assertIn("tilted_window_not_explicitly_safe_for_blind", trace.reasons)

    def test_fully_open_window_uses_safe_position_not_policy_target(self) -> None:
        inputs = replace(ready_inputs(), opening_state=fresh("open", "opening_contract"))
        trace = DecisionEngine().evaluate(inputs)

        self.assertEqual(trace.safety.status, "safe_position")
        self.assertEqual(trace.effective_target, 100)
        self.assertEqual(trace.apply.status, "safety_ready")
        self.assertEqual(trace.apply.reason, "safety_target_bypasses_normal_cooldown")

    def test_positive_opening_safety_uses_axis_specific_safe_open_position(self) -> None:
        inputs = replace(ready_inputs(), opening_state=fresh("open", "opening_contract"))
        normal = DecisionEngine().evaluate(inputs)
        inverted = DecisionEngine(
            replace(BlindControlConfig.defaults(), axis_inverted=True)
        ).evaluate(inputs)

        self.assertEqual(normal.effective_target, 100)
        self.assertEqual(inverted.effective_target, 100)
        self.assertEqual(inverted.safety.status, "safe_position")

    def test_stale_opening_does_not_become_closed(self) -> None:
        inputs = replace(ready_inputs(), opening_state=stale("closed", "opening_contract"))
        trace = DecisionEngine().evaluate(inputs)

        self.assertEqual(trace.safety.status, "blocked")
        self.assertIsNone(trace.effective_target)
        self.assertEqual(trace.safety.opening_state, "unknown")

    def test_unusable_opening_quality_never_creates_opening_drive(self) -> None:
        for quality in (
            InputQuality.UNKNOWN,
            InputQuality.STALE,
            InputQuality.UNAVAILABLE,
            InputQuality.CONFLICT,
        ):
            with self.subTest(quality=quality):
                inputs = replace(
                    ready_inputs(),
                    opening_state=InputObservation(
                        value="open",
                        source="opening_contract",
                        quality=quality,
                        reason=f"opening_{quality.value}",
                    ),
                )
                trace = DecisionEngine().evaluate(inputs)

                self.assertEqual(trace.safety.status, "blocked")
                self.assertIsNone(trace.effective_target)
                self.assertNotEqual(trace.effective_target, 100)

    def test_known_neutral_context_is_normal_not_failure(self) -> None:
        neutral = DecisionEngine().evaluate(
            replace(ready_inputs(), day_state=fresh("night", "core_state.day"))
        )

        self.assertEqual(neutral.master_mode.value, "normal")
        self.assertEqual(neutral.failure.status, "none")
        self.assertIsNone(neutral.fachlicher_target)
        self.assertEqual(neutral.winner.category, "neutral")
        self.assertEqual(neutral.winner.candidate_key, "neutral_context")

    def test_failure_holds_last_proven_safe_position_or_blocks_apply(self) -> None:
        failed_inputs = replace(ready_inputs(), day_state=stale("morning", "core_state.day"))
        runtime_with_safe_position = ShadowRuntime()
        runtime_with_safe_position.evaluate(ready_inputs(), now=0)
        held = runtime_with_safe_position.evaluate(failed_inputs, now=1).trace
        blocked = (
            ShadowRuntime()
            .evaluate(
                replace(failed_inputs, cover_position=InputObservation.missing("technical_cover")),
                now=1,
            )
            .trace
        )

        self.assertEqual(held.master_mode.value, "normal")
        self.assertFalse(held.failure.active)
        self.assertIsNone(held.effective_target)
        self.assertEqual(held.apply.status, "idle")
        self.assertFalse(held.apply.write_path_reachable)
        self.assertNotEqual(held.effective_target, 100)
        self.assertEqual(blocked.safety.status, "blocked")
        self.assertIsNone(blocked.effective_target)
        self.assertEqual(blocked.apply.status, "blocked")

    def test_storm_releases_heat_but_tv_glare_remains(self) -> None:
        inputs = sunny_inputs(
            activity_state=fresh("console", "core_state.activity"),
            outdoor_temperature=fresh(34.0, "weather_temperature"),
            weather_alert=fresh(True, "weather_alert"),
            precipitation_trend=fresh(1.0, "weather_trend"),
            wind_trend=fresh(1.0, "weather_trend"),
        )
        trace = DecisionEngine().evaluate(inputs)

        self.assertTrue(
            next(item for item in trace.candidates if item.key == "storm_approaching").active
        )
        self.assertIn("glare_tv", trace.winner_keys)
        self.assertNotIn("heat_protection", trace.winner_keys)
        self.assertEqual(trace.fachlicher_target, 60)

    def test_storm_and_cool_air_are_separate_candidates(self) -> None:
        cool_air = replace(
            ready_inputs(),
            day_state=fresh("early_morning", "core_state.day"),
            sun_elevation=fresh(-5.0, "sun_contract"),
            outdoor_temperature=fresh(20.0, "weather_temperature"),
            indoor_temperature=fresh(24.0, "room_temperature"),
            air_movement=fresh(True, "air_quality_contract"),
        )
        trace = DecisionEngine().evaluate(cool_air)

        self.assertTrue(
            next(item for item in trace.candidates if item.key == "cool_air_available").active
        )
        self.assertFalse(
            next(item for item in trace.candidates if item.key == "storm_approaching").active
        )
        self.assertNotIn("storm_approaching", trace.reasons)

    def test_glare_requires_window_solar_relevance_at_night_and_off_window(self) -> None:
        night = replace(
            sunny_inputs(),
            activity_state=fresh("pc", "core_state.activity"),
            sun_elevation=fresh(-5.0, "sun_contract"),
            outdoor_lux=fresh(10.0, "lux_sensor"),
        )
        off_window = replace(
            sunny_inputs(),
            activity_state=fresh("pc", "core_state.activity"),
            sun_azimuth=fresh(304.0, "sun_contract"),
        )

        night_trace = DecisionEngine().evaluate(night)
        off_window_trace = DecisionEngine().evaluate(off_window)

        self.assertFalse(
            next(item for item in night_trace.candidates if item.key == "glare_pc").active
        )
        self.assertFalse(
            next(item for item in off_window_trace.candidates if item.key == "glare_pc").active
        )
        self.assertNotIn("glare_pc", night_trace.winner_keys)
        self.assertNotIn("glare_pc", off_window_trace.winner_keys)

    def test_cool_air_opens_only_when_no_closing_candidate_is_active(self) -> None:
        inputs = replace(
            ready_inputs(),
            day_state=fresh("early_morning", "core_state.day"),
            sun_elevation=fresh(-5.0, "sun_contract"),
            outdoor_temperature=fresh(20.0, "weather_temperature"),
            indoor_temperature=fresh(24.0, "room_temperature"),
            air_movement=fresh(True, "air_quality_contract"),
        )
        trace = DecisionEngine().evaluate(inputs)

        self.assertIn("cool_air_available", trace.winner_keys)
        self.assertEqual(trace.fachlicher_target, 100)
        self.assertIn("cooler_moving_outdoor_air_available", trace.reasons)

    def test_axis_inversion_keeps_logical_arbitration(self) -> None:
        config = replace(BlindControlConfig.defaults(), axis_inverted=True)
        inputs = sunny_inputs(
            outdoor_temperature=fresh(34.0, "weather_temperature"),
        )

        trace = DecisionEngine(config).evaluate(inputs)

        self.assertEqual(trace.fachlicher_target, 15)
        self.assertEqual(config.target("heat_protection"), 15)
        self.assertEqual(config.device_position(15), 85)

    def test_config_round_trip_keeps_logical_and_derived_complement(self) -> None:
        config = replace(BlindControlConfig.defaults(), axis_inverted=True)
        restored = BlindControlConfig.from_mapping(config.to_mapping())

        self.assertTrue(restored.axis_inverted)
        self.assertEqual(restored.profile("glare_pc").logical, 75)
        self.assertEqual(restored.profile("glare_pc").inverted, 25)


class SolarAndLifecycleTests(unittest.TestCase):
    def test_solar_geometry_golden_vectors(self) -> None:
        direct = calculate_solar_exposure(sunny_inputs(), BlindControlConfig.defaults())
        diffuse = calculate_solar_exposure(
            replace(
                sunny_inputs(),
                expected_direct_radiation=fresh(50.0, "weather_model"),
                expected_diffuse_radiation=fresh(100.0, "weather_model"),
                outdoor_lux=fresh(3_000.0, "lux_sensor"),
            ),
            BlindControlConfig.defaults(),
        )
        away_from_window = calculate_solar_exposure(
            replace(sunny_inputs(), sun_azimuth=fresh(304.0, "sun_contract")),
            BlindControlConfig.defaults(),
        )
        night = calculate_solar_exposure(
            replace(sunny_inputs(), sun_elevation=fresh(-2.0, "sun_contract")),
            BlindControlConfig.defaults(),
        )

        self.assertEqual(direct.state, SolarExposureState.DIRECT_SUN)
        self.assertAlmostEqual(direct.incidence_factor, 0.866, places=2)
        self.assertEqual(diffuse.state, SolarExposureState.DIFFUSE_BRIGHT)
        self.assertEqual(away_from_window.state, SolarExposureState.SOLAR_NOT_ON_WINDOW)
        self.assertEqual(night.state, SolarExposureState.NIGHT)

    def test_fresh_positive_sun_elevation_overrides_low_lux_night_fallback(self) -> None:
        inputs = replace(
            sunny_inputs(),
            sun_elevation=fresh(12.0, "sun_contract"),
            sun_azimuth=fresh(124.0, "sun_contract"),
            outdoor_lux=fresh(1.0, "lux_sensor"),
            expected_direct_radiation=fresh(0.0, "weather_model"),
            expected_diffuse_radiation=fresh(0.0, "weather_model"),
        )

        exposure = calculate_solar_exposure(inputs, BlindControlConfig.defaults())

        self.assertNotEqual(exposure.state, SolarExposureState.NIGHT)
        self.assertEqual(exposure.state, SolarExposureState.LOW_LIGHT)
        self.assertEqual(exposure.reason, "active_sun_with_low_observed_light")

    def test_override_lifecycle_distinguishes_owned_external_restart_and_config(self) -> None:
        runtime = ShadowRuntime()
        runtime.on_restart(50)
        runtime.begin_own_write(20, now=10, grace_seconds=10)
        runtime.observe_cover_position(40, source="owned_position", now=12)
        runtime.observe_cover_position(20, source="owned_position", now=14)
        runtime.observe_cover_position(20, source="owned_position", now=16)
        self.assertFalse(runtime.override.active)

        runtime.observe_cover_position(80, source="foreign_position", now=20)
        runtime.observe_cover_position(80, source="foreign_position", now=22)
        self.assertTrue(runtime.override.active)
        self.assertEqual(runtime.override.baseline, 20)
        runtime.clear_override()
        self.assertFalse(runtime.observe_cover_position(80, source="same_position", now=23).active)
        self.assertFalse(runtime.observe_cover_position(70, source="new_position", now=24).active)
        self.assertTrue(runtime.observe_cover_position(70, source="new_position", now=26).active)
        runtime.clear_override()
        runtime.on_configuration_change(80)
        self.assertFalse(runtime.override.active)
        runtime.on_restart(80)
        runtime.observe_cover_position(80, source="restored_position", now=30)
        self.assertFalse(runtime.override.active)

    def test_config_change_recomputes_without_creating_override(self) -> None:
        runtime = ShadowRuntime()
        inputs = ready_inputs()
        snapshot = runtime.update_config(
            replace(BlindControlConfig.defaults(), axis_inverted=True),
            inputs,
            now=0,
        )

        self.assertEqual(snapshot.trace.fachlicher_target, 100)
        self.assertEqual(snapshot.physical_target, 0)
        self.assertFalse(snapshot.trace.override.active)

    def test_legacy_shadow_diff_is_fieldwise_and_classified(self) -> None:
        snapshot = ShadowRuntime().evaluate(
            BlindControlInputs.empty(),
            now=0,
            legacy_snapshot={"effective_target": 100, "safety_status": "ready"},
        )

        self.assertEqual(len(snapshot.diffs), 2)
        self.assertEqual(snapshot.diffs[0].classification, DiffClassification.IMPROVED)
        self.assertEqual(snapshot.diffs[1].classification, DiffClassification.IMPROVED)

    def test_ux_projection_is_versioned_and_read_only(self) -> None:
        runtime = ShadowRuntime()
        snapshot = runtime.evaluate(ready_inputs(), now=0)
        projection = build_ux_snapshot(snapshot, runtime.config)

        self.assertEqual(projection["version"], UX_CONTRACT_VERSION)
        self.assertIn("overview", projection)
        self.assertIn("diagnosis", projection)
        self.assertIn("settings", projection)
        self.assertIn("debug_payload", projection)
        self.assertFalse(projection["debug_payload"]["write_path_reachable"])

    def test_debug_payload_redacts_owner_bound_sources(self) -> None:
        snapshot = ShadowRuntime().evaluate(
            replace(ready_inputs(), bio_state=fresh("awake", "sensor.bound_bio")), now=0
        )
        debug_payload = snapshot.debug_payload()

        self.assertEqual(debug_payload["inputs"]["bio_state"]["source"], "owner_bound")
        self.assertNotIn("sensor.bound_bio", repr(debug_payload))
        self.assertNotIn("core_state.day", repr(debug_payload))

    def test_latest_target_only_cooldown(self) -> None:
        tracker = CooldownTracker(tolerance=0)
        first = tracker.propose(20, now=0, cooldown_seconds=60)
        tracker.record_write(20, now=0, cooldown_seconds=60)
        second = tracker.propose(70, now=10, cooldown_seconds=60)
        third = tracker.propose(40, now=20, cooldown_seconds=60)
        released = tracker.propose(40, now=60, cooldown_seconds=60)

        self.assertTrue(first.apply_now)
        self.assertFalse(second.apply_now)
        self.assertFalse(third.apply_now)
        self.assertEqual(second.pending_target, 70)
        self.assertEqual(third.pending_target, 40)
        self.assertTrue(released.apply_now)
        self.assertEqual(released.target, 40)


if __name__ == "__main__":
    unittest.main()
