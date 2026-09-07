"""v0.6.1 regressions: HA handler semantics, recovery and environmental transitions."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_apply import FakeHass, FakeServices, config_for, fresh, ready_inputs
from test_coordinator import FakeState

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.contracts import InputObservation, InputQuality
from custom_components.blind_control.coordinator import build_inputs_from_states
from custom_components.blind_control.engine import DecisionEngine
from custom_components.blind_control.shadow import ShadowRuntime
from custom_components.blind_control.solar import calculate_solar_exposure
from custom_components.blind_control.ux_contract import build_ux_snapshot


def active(snapshot, key):
    return next(item.active for item in snapshot.trace.candidates if item.key == key)


def test_ha_nonblocking_failure_is_background_only_and_blocking_propagates():
    async def scenario():
        services = FakeServices(fail=True)
        await services.async_call("cover", "set_cover_position", {}, blocking=False)
        await asyncio.gather(*services.tasks)
        assert len(services.background_errors) == 1
        with pytest.raises(RuntimeError):
            await services.async_call("cover", "set_cover_position", {}, blocking=True)

    asyncio.run(scenario())


@pytest.mark.parametrize("error", ["command_error", "target_not_reached"])
def test_failed_motion_quiet_recovery_rebases_and_uses_latest_target(error):
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass(fail=error == "command_error")
        adapter = CoverApplyExecutor(hass, config, runtime)
        first = await adapter.async_apply(runtime.evaluate(ready_inputs(), now=0), now=0)
        if error == "command_error":
            assert first.trace.apply.status == "error"
            assert not first.actuation_executed and not first.trace.apply.executed
            assert runtime.cooldown_tracker.last_applied_target is None
            assert runtime.cooldown_tracker.cooldown_until == 0
            assert first.movement_error == error
        else:
            assert first.trace.apply.status == "applied"
            runtime.observe_cover_position(60, now=121, moving=True)
        assert runtime.override_tracker.motion_status == error
        # Changing intentions during failure neither writes nor makes an override.
        current = ready_inputs(activity_state=fresh("pc"), cover_position=fresh(60))
        for now in (122, 125, 130):
            blocked = await adapter.async_apply(runtime.evaluate(current, now=now), now=now)
            assert not blocked.actuation_executed
            assert not runtime.override.active
        assert len(hass.services.calls) == 1
        runtime.observe_cover_position(60, now=131)
        runtime.observe_cover_position(60, now=160)
        assert runtime.override_tracker.own_target == 100
        runtime.observe_cover_position(60, now=161)
        assert runtime.override_tracker.own_target is None
        assert runtime.override_tracker.baseline == 60
        assert runtime.override_tracker.recovery_status == "recovered"
        assert not runtime.override.active
        hass.services.fail = False
        latest = await adapter.async_apply(runtime.evaluate(current, now=162), now=162)
        assert latest.trace.apply.status == "applied"
        assert [call[2]["position"] for call in hass.services.calls] == [100, 75]
        assert all(call[3] for call in hass.services.calls)
        projection = build_ux_snapshot(latest, config)
        assert projection["overview"]["movement_error"] == error
        assert projection["overview"]["recovery_status"] == "recovered"

    asyncio.run(scenario())


@pytest.mark.parametrize("error", ["command_error", "target_not_reached"])
@pytest.mark.parametrize("inverted", [False, True])
def test_safety_during_failed_motion_is_immediate(error, inverted):
    async def scenario():
        config = replace(config_for("live", "blind_control"), axis_inverted=inverted)
        runtime = ShadowRuntime(config)
        runtime.on_restart(60)
        runtime.begin_own_write(15, now=0)
        if error == "command_error":
            runtime.abort_own_write()
        else:
            runtime.observe_cover_position(50, now=121, moving=True)
        inputs = ready_inputs(
            opening_state=fresh("open"),
            cover_position=fresh(50),
            cover_motion=fresh("closing"),
            outdoor_temperature=fresh(34),
        )
        hass = FakeHass()
        result = await CoverApplyExecutor(hass, config, runtime).async_apply(
            runtime.evaluate(inputs, now=122), now=122
        )
        assert result.actuation_executed
        assert hass.services.calls[0][2]["position"] == (0 if inverted else 100)
        assert not runtime.override.active

    asyncio.run(scenario())


@pytest.mark.parametrize("interruption", ["moving", "unavailable", "position_change"])
def test_recovery_requires_continuous_new_quiet_evidence(interruption):
    runtime = ShadowRuntime()
    runtime.on_restart(42)
    runtime.begin_own_write(100, now=0)
    runtime.abort_own_write()
    runtime.observe_cover_position(42, now=1)
    if interruption == "moving":
        runtime.observe_cover_position(42, now=20, moving=True)
    elif interruption == "unavailable":
        runtime.observe_cover_position(None, now=20)
    else:
        runtime.observe_cover_position(60, now=20)
    runtime.observe_cover_position(42, now=21)
    runtime.observe_cover_position(42, now=31)
    assert runtime.override_tracker.own_target == 100
    runtime.observe_cover_position(42, now=51)
    assert runtime.override_tracker.own_target is None
    assert not runtime.override.active


def test_cold_boundary_oscillation_and_sustained_brightness():
    runtime = ShadowRuntime()

    def sample(lux, now):
        return runtime.evaluate(
            ready_inputs(outdoor_lux=fresh(lux), outdoor_temperature=fresh(5)), now=now
        )

    assert not active(sample(390, 0), "cold_insulation")
    assert active(sample(390, 10), "cold_insulation")
    for now, lux in enumerate((410, 395, 420, 390, 410), 11):
        assert active(sample(lux, now), "cold_insulation")
    assert active(sample(500, 20), "cold_insulation")
    assert active(sample(1000, 21), "cold_insulation")
    assert active(sample(1000, 140), "cold_insulation")
    assert not active(sample(1000, 141), "cold_insulation")


def test_glare_short_cloud_keeps_protection_and_sustained_relief_exits():
    runtime = ShadowRuntime()
    sunny = ready_inputs(activity_state=fresh("pc"))
    runtime.evaluate(sunny, now=0)
    assert active(runtime.evaluate(sunny, now=10), "glare_pc")
    cloud = replace(sunny, cloud_cover=fresh(100), outdoor_lux=fresh(4000))
    assert active(runtime.evaluate(cloud, now=11), "glare_pc")
    # Positive geometric relief, not unknown-as-relief.
    relief = replace(sunny, sun_azimuth=fresh(304))
    assert active(runtime.evaluate(relief, now=20), "glare_pc")
    assert active(runtime.evaluate(sunny, now=30), "glare_pc")
    assert runtime.environment_state.glare.pending is None
    assert active(runtime.evaluate(relief, now=40), "glare_pc")
    assert active(runtime.evaluate(relief, now=159), "glare_pc")
    assert not active(runtime.evaluate(relief, now=160), "glare_pc")


def test_confidence_and_solar_geometry_have_real_enter_exit_bands():
    config = BlindControlConfig.defaults()
    engine = DecisionEngine(config)
    solar = calculate_solar_exposure(ready_inputs(), config)
    mid_confidence = replace(solar, confidence=0.30)
    assert not engine._glare_relevant(mid_confidence)
    assert engine._glare_relevant(mid_confidence, held=True)
    from custom_components.blind_control.contracts import SolarExposureState

    edge = replace(solar, state=SolarExposureState.SOLAR_NOT_ON_WINDOW, incidence_factor=0.045)
    assert not engine._glare_relevant(edge)
    assert engine._glare_relevant(edge, held=True)
    assert not engine._glare_relevant(replace(edge, incidence_factor=0.039), held=True)
    hot = ready_inputs(outdoor_temperature=fresh(34))
    assert not engine._heat_active(hot, replace(solar, confidence=0.5), False)[0]
    assert engine._heat_active(hot, replace(solar, confidence=0.5), False, held=True)[0]


def test_debounce_latest_state_no_old_activity_target_and_immediate_safety_waking():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        adapter = CoverApplyExecutor(hass, config, runtime)
        tv = ready_inputs(activity_state=fresh("tv"))
        pending = runtime.evaluate(tv, now=0)
        assert pending.trace.apply.reason == "environment_protection_stabilizing"
        await adapter.async_apply(pending, now=0)
        assert not hass.services.calls
        wake = runtime.evaluate(replace(tv, bio_state=fresh("waking")), now=1)
        assert wake.trace.apply.status == "live_ready"
        assert wake.effective_target == 100
        safe = runtime.evaluate(replace(tv, opening_state=fresh("open")), now=2)
        assert safe.trace.apply.status == "safety_ready"
        # Do not dispatch these two different approvals; test the latest PC state.
        pc = runtime.evaluate(ready_inputs(activity_state=fresh("pc")), now=10)
        await adapter.async_apply(pc, now=10)
        assert [call[2]["position"] for call in hass.services.calls] == [75]

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "hard_state", ["safety", "waking", "sleep", "provisional_sleep", "privacy", "away"]
)
def test_hard_states_can_dispatch_during_environment_entry(hard_state):
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        inputs = ready_inputs(activity_state=fresh("tv"))
        assert (
            runtime.evaluate(inputs, now=0).trace.apply.reason
            == "environment_protection_stabilizing"
        )
        changes = (
            {"opening_state": fresh("open")}
            if hard_state == "safety"
            else {"bio_state": fresh(hard_state)}
            if hard_state in {"waking", "sleep", "provisional_sleep"}
            else {hard_state: fresh(True)}
        )
        hass = FakeHass()
        result = await CoverApplyExecutor(hass, config, runtime).async_apply(
            runtime.evaluate(replace(inputs, **changes), now=1), now=1
        )
        assert result.actuation_executed
        assert len(hass.services.calls) == 1
        assert result.trace.apply.reason != "environment_protection_stabilizing"

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "quality", [InputQuality.STALE, InputQuality.UNAVAILABLE, InputQuality.CONFLICT]
)
def test_invalid_lux_cannot_start_cold_or_complete_a_pending_transition(quality):
    runtime = ShadowRuntime()
    cold = ready_inputs(outdoor_lux=fresh(390), outdoor_temperature=fresh(5))
    runtime.evaluate(cold, now=0)
    bad = replace(cold, outdoor_lux=InputObservation(value=390, source="owner", quality=quality))
    result = runtime.evaluate(bad, now=10)
    assert not active(result, "cold_insulation")
    assert result.trace.failure.active and not result.write_path_reachable
    assert not active(runtime.evaluate(cold, now=11), "cold_insulation")
    assert active(runtime.evaluate(cold, now=21), "cold_insulation")


@pytest.mark.parametrize("motion", ["opening", "closing", "open", "closed"])
@pytest.mark.parametrize("inverted", [False, True])
def test_axis_inversion_transforms_only_numeric_position(motion, inverted):
    now = datetime.now(UTC)
    config = BlindControlConfig.from_mapping(
        {"axis_inverted": inverted, "input_bindings": {"cover_position": "cover.fixture"}}
    )
    values = build_inputs_from_states(
        {"cover.fixture": FakeState(motion, attributes={"current_position": 70}, updated_at=now)},
        config,
        now=now,
    )
    assert values.cover_motion.value == motion
    assert values.cover_position.value == (30 if inverted else 70)


def test_v060_config_v6_load_and_roundtrip_preserves_every_existing_value():
    # Neutral fixture produced by the unmodified v0.6.0 serializer at 303d843.
    # Includes all old fields; CI needs neither Git history nor Home Assistant.
    old = json.loads((Path(__file__).parent / "fixtures/v060_config.json").read_text())
    loaded = BlindControlConfig.from_mapping(old)
    new = loaded.to_mapping()
    for key, value in old.items():
        assert new["cold_lux_enter_threshold" if key == "cold_lux_threshold" else key] == value
    assert loaded.cold_lux_exit_threshold == 812.5
    assert loaded.movement_recovery_seconds == 40
    assert BlindControlConfig.from_mapping(json.loads(json.dumps(new))) == loaded
    assert new["config_version"] == 6


@pytest.mark.parametrize(
    "changes",
    [
        {"cold_lux_enter_threshold": 500, "cold_lux_exit_threshold": 500},
        {"cold_lux_exit_threshold": 399},
        {"environment_enter_seconds": 0},
        {"environment_exit_seconds": 5},
        {"environment_hysteresis_ratio": 1},
        {"movement_recovery_seconds": 1},
    ],
)
def test_new_calibration_rejects_invalid_bands_and_durations(changes):
    with pytest.raises(ValueError):
        BlindControlConfig.from_mapping(changes)


def test_handler_must_finish_before_success_but_motion_remains_unverified():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        entered, release = asyncio.Event(), asyncio.Event()

        async def handler():
            entered.set()
            await release.wait()

        hass.services._handler = handler
        adapter = CoverApplyExecutor(hass, config, runtime)
        approval = runtime.evaluate(ready_inputs(), now=0)
        task = asyncio.create_task(adapter.async_apply(approval, now=0))
        await entered.wait()
        assert not task.done()
        assert runtime.cooldown_tracker.last_applied_target is None
        await adapter.async_apply(approval, now=1)
        assert len(hass.services.calls) == 1
        release.set()
        result = await task
        assert result.trace.apply.status == "applied"
        assert runtime.override_tracker.own_target == 100
        assert runtime.override_tracker.baseline == 42

    asyncio.run(scenario())


def test_real_optional_confidence_fluctuation_retains_then_releases_glare():
    runtime = ShadowRuntime(replace(BlindControlConfig.defaults(), glare_confidence_threshold=0.95))
    sunny = ready_inputs(activity_state=fresh("pc"))
    runtime.evaluate(sunny, now=0)
    assert active(runtime.evaluate(sunny, now=10), "glare_pc")
    within_band = replace(sunny, cloud_cover=InputObservation())
    held = runtime.evaluate(within_band, now=20)
    assert held.trace.solar.confidence < 0.95
    assert active(held, "glare_pc")
    relief = replace(
        within_band,
        expected_direct_radiation=InputObservation(),
        expected_diffuse_radiation=InputObservation(),
    )
    assert active(runtime.evaluate(relief, now=30), "glare_pc")
    assert not active(runtime.evaluate(relief, now=150), "glare_pc")


def test_heat_stabilization_retains_heat_then_falls_back_to_current_pc():
    runtime = ShadowRuntime()
    hot = ready_inputs(activity_state=fresh("pc"), outdoor_temperature=fresh(34))
    runtime.evaluate(hot, now=0)
    assert runtime.evaluate(hot, now=10).trace.winner_keys == ("heat_protection",)
    mild = replace(hot, outdoor_temperature=fresh(20))
    assert runtime.evaluate(mild, now=20).trace.winner_keys == ("heat_protection",)
    assert runtime.evaluate(mild, now=140).trace.winner_keys == ("glare_pc",)


def test_new_defaults_are_visible_and_non_default_calibration_roundtrips():
    values = {
        "cold_lux_enter_threshold": 300,
        "cold_lux_exit_threshold": 650,
        "environment_hysteresis_ratio": 0.7,
        "environment_enter_seconds": 20,
        "environment_exit_seconds": 90,
        "movement_recovery_seconds": 45,
    }
    config = BlindControlConfig.from_mapping(values)
    assert BlindControlConfig.from_mapping(config.to_mapping()).to_mapping() == config.to_mapping()
    ux = build_ux_snapshot(ShadowRuntime(config).evaluate(ready_inputs()), config)
    assert all(
        ux["settings"]["calibration_defaults"][key] == value for key, value in values.items()
    )
