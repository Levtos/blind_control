"""AP3 regressions against real runtime, adapter and input-normalization boundaries."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from test_apply import FakeHass, config_for, fresh, ready_inputs
from test_coordinator import FakeEntry, FakeState, ThreadAwareFakeHass

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.contracts import InputObservation, InputQuality
from custom_components.blind_control.coordinator import ShadowCoordinator, build_inputs_from_states
from custom_components.blind_control.engine import DecisionEngine
from custom_components.blind_control.shadow import ShadowRuntime


def test_safety_repeats_from_actual_position_in_both_axes():
    async def scenario(inverted):
        config = replace(config_for("live", "blind_control"), axis_inverted=inverted)
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        adapter = CoverApplyExecutor(hass, config, runtime)
        inputs = ready_inputs(opening_state=fresh("open"))
        await adapter.async_apply(runtime.evaluate(inputs, now=10), now=10)
        runtime.observe_cover_position(100, now=11)
        runtime.observe_cover_position(100, now=13)
        runtime.observe_cover_position(60, now=14)
        runtime.observe_cover_position(60, now=16)
        assert runtime.override.active
        current = replace(inputs, cover_position=fresh(60))
        await adapter.async_apply(runtime.evaluate(current, now=17), now=17)
        assert [call[2]["position"] for call in hass.services.calls] == [
            0 if inverted else 100,
            0 if inverted else 100,
        ]

    for inverted in (False, True):
        asyncio.run(scenario(inverted))


def test_open_supersedes_own_downward_motion_and_pending_intent():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        adapter = CoverApplyExecutor(hass, config, runtime)
        await adapter.async_apply(
            runtime.evaluate(ready_inputs(bio_state=fresh("sleep")), now=10), now=10
        )
        runtime.cooldown_tracker.pending_target = 15
        runtime.observe_cover_position(30, now=11, moving=True)
        current = ready_inputs(
            opening_state=fresh("open"),
            cover_position=fresh(30),
            cover_motion=fresh("closing"),
            bio_state=fresh("waking"),
        )
        snapshot = runtime.evaluate(current, now=11)
        assert snapshot.trace.apply.status == "safety_ready"
        assert runtime.cooldown_tracker.pending_target is None
        await adapter.async_apply(snapshot, now=11)
        assert [call[2]["position"] for call in hass.services.calls] == [5, 100]
        assert runtime.override_tracker.own_target == 100
        assert not runtime.override.active

    asyncio.run(scenario())


def test_safety_never_lowers_position_even_with_lower_configured_safe_target():
    config = BlindControlConfig.from_mapping({"profiles": {"window_safety": {"logical": 60}}})
    trace = DecisionEngine(config).evaluate(
        ready_inputs(opening_state=fresh("open"), cover_position=fresh(80))
    )
    assert trace.effective_target == 80


def test_open_and_tilted_are_distinct_and_owner_handover_keeps_safety():
    engine = DecisionEngine()
    # Canonical aggregate values, not a second raw-contact fusion in the consumer.
    for owner_value in ("open", "open", "open", "closed"):
        trace = engine.evaluate(
            ready_inputs(opening_state=fresh(owner_value), bio_state=fresh("sleep"))
        )
        assert trace.effective_target == (100 if owner_value == "open" else 5)
    tilted = engine.evaluate(
        ready_inputs(
            opening_state=fresh("tilted"),
            opening_safe_for_blind=fresh(True),
            bio_state=fresh("sleep"),
        )
    )
    assert tilted.effective_target == 5


def test_revoked_consumed_and_outdated_approvals_cannot_write():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        adapter = CoverApplyExecutor(hass, config, runtime)
        old = runtime.evaluate(ready_inputs(), now=10)
        newest = runtime.evaluate(ready_inputs(activity_state=fresh("pc")), now=11)
        await adapter.async_apply(old, now=11)
        assert not hass.services.calls
        await adapter.async_apply(newest, now=11)
        await adapter.async_apply(newest, now=12)
        assert len(hass.services.calls) == 1
        runtime.stop()
        await adapter.async_apply(newest, now=13)
        with pytest.raises(RuntimeError, match="runtime_stopped"):
            runtime.evaluate(ready_inputs())
        assert len(hass.services.calls) == 1

        other = ShadowRuntime(config)
        other.on_restart(42)
        approval = other.evaluate(ready_inputs())
        other.config = replace(config, apply_enabled=False)
        await CoverApplyExecutor(hass, config, other).async_apply(approval)
        assert len(hass.services.calls) == 1

    asyncio.run(scenario())


def test_queued_callback_and_refresh_after_stop_are_permanently_dead():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        hass = ThreadAwareFakeHass({}, asyncio.get_running_loop())
        hass.services = FakeHass().services
        coordinator = ShadowCoordinator(hass, FakeEntry(), config, runtime)
        coordinator._schedule_refresh()
        coordinator.stop()
        await asyncio.sleep(0)
        coordinator._schedule_refresh_in_event_loop()
        coordinator._refresh_requested = True
        coordinator._refresh_finished(None)
        assert hass.tasks == []
        assert hass.services.calls == []
        with pytest.raises(RuntimeError, match="runtime_stopped"):
            await coordinator.async_refresh()

    asyncio.run(scenario())


def test_solar_unknown_holds_but_positive_opening_safety_is_independent():
    inputs = ready_inputs(
        outdoor_lux=fresh(500),
        sun_elevation=fresh(30),
        expected_direct_radiation=InputObservation(),
        expected_diffuse_radiation=InputObservation(),
        cloud_cover=InputObservation(),
        lux_trend=InputObservation(),
    )
    trace = DecisionEngine().evaluate(inputs)
    assert trace.solar.state.value == "unknown"
    assert trace.apply.approved_target is None
    assert trace.failure.active
    safety = DecisionEngine().evaluate(replace(inputs, opening_state=fresh("open")))
    assert safety.effective_target == 100
    assert safety.safety.status == "safe_position"


def test_own_motion_requires_stable_target_not_timeout_and_restart_is_not_override():
    runtime = ShadowRuntime()
    runtime.on_restart(50)
    runtime.begin_own_write(20, now=0, grace_seconds=5)
    for now, position in ((1, 40), (3, 30), (6, 25), (7, 24)):
        runtime.observe_cover_position(position, now=now, moving=True)
        assert not runtime.override.active
    assert runtime.override_tracker.motion_status == "target_not_reached"
    runtime.observe_cover_position(20, now=8)
    assert runtime.override_tracker.own_target == 20
    runtime.observe_cover_position(20, now=10)
    assert runtime.override_tracker.own_target is None
    runtime.observe_cover_position(60, now=11)
    assert not runtime.override.active
    runtime.observe_cover_position(60, now=13)
    assert runtime.override.active

    runtime.on_restart(None)
    for now, position in ((20, 50), (21, 40)):
        runtime.observe_cover_position(position, now=now, moving=True)
        assert not runtime.override.active
        assert not runtime.override_tracker.initialized
    runtime.observe_cover_position(30, now=22)
    runtime.observe_cover_position(30, now=24)
    assert runtime.override_tracker.initialized
    assert runtime.override_tracker.baseline == 30
    assert not runtime.override.active


@pytest.mark.parametrize(
    "lux,quality,active",
    [
        (399, InputQuality.FRESH, True),
        (400, InputQuality.FRESH, False),
        (1000, InputQuality.FRESH, False),
        (None, InputQuality.UNKNOWN, False),
        (1, InputQuality.STALE, False),
    ],
)
def test_cold_requires_real_fresh_darkness(lux, quality, active):
    inputs = ready_inputs(
        outdoor_temperature=fresh(-5),
        sun_azimuth=fresh(304),
        outdoor_lux=InputObservation(value=lux, quality=quality),
    )
    trace = DecisionEngine().evaluate(inputs)
    cold = next(c for c in trace.candidates if c.key == "cold_insulation")
    assert cold.active is active


@pytest.mark.parametrize("logical", [60, 30, 75, 85, 50])
def test_axis_only_changes_device_value(logical):
    inputs = ready_inputs(activity_state=fresh("pc"))
    traces = []
    for inverted in (False, True):
        config = BlindControlConfig.from_mapping(
            {
                "axis_inverted": inverted,
                "profiles": {"glare_pc": {"logical": logical}},
            }
        )
        trace = DecisionEngine(config).evaluate(inputs)
        traces.append(trace)
        assert config.device_position(trace.effective_target) == (
            100 - logical if inverted else logical
        )
    assert traces[0].as_dict() == traces[1].as_dict()


@pytest.mark.parametrize("cloud", [0, 75, 100])
def test_cloud_percent_and_physical_input_normalization(cloud):
    now = datetime.now(UTC)
    config = BlindControlConfig.from_mapping(
        {
            "axis_inverted": True,
            "input_bindings": {
                "cover_position": "cover.fixture",
                "cloud_cover": "sensor.fixture_cloud",
            },
        }
    )
    states = {
        "cover.fixture": FakeState("closing", attributes={"current_position": 70}, updated_at=now),
        "sensor.fixture_cloud": FakeState(str(cloud), updated_at=now),
    }
    inputs = build_inputs_from_states(states, config, now=now)
    assert inputs.cover_position.value == 30
    assert inputs.cover_motion.value == "opening"
    assert inputs.cloud_cover.value == cloud
    states["sensor.fixture_cloud"] = FakeState("101", updated_at=now)
    assert not build_inputs_from_states(states, config, now=now).cloud_cover.usable


def test_config_v5_migration_preserves_old_values_and_does_not_change_meaning():
    old = {
        "config_version": 5,
        "axis_inverted": True,
        "cloud_shadow_ratio": 0.8,
        "profiles": {
            "heat_protection": {"normal": 17, "inverted": 55},
            "glare_pc": {"normal": 60, "inverted": 10},
        },
    }
    config = BlindControlConfig.from_mapping(old)
    assert config.target("heat_protection") == 17
    assert config.device_position(17) == 83
    saved = config.to_mapping()
    assert saved["config_version"] == 6
    assert saved["cloud_cover_threshold"] == 80
    assert saved["model_lux_ratio"] == 0.8
    assert saved["profiles"]["glare_pc"] == {"logical": 60}
    assert saved["legacy_profile_values"] == old["profiles"]
    assert BlindControlConfig.from_mapping(saved).to_mapping() == saved
    assert old["profiles"]["heat_protection"]["inverted"] == 55
    assert (
        BlindControlConfig.from_mapping({"cold_outdoor_threshold": -3}).cold_outdoor_threshold == -3
    )
    with pytest.raises(ValueError):
        BlindControlConfig.from_mapping({"config_version": 999})


def test_coordinator_restart_during_motion_uses_quiet_actual_baseline():
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        hass = ThreadAwareFakeHass({}, asyncio.get_running_loop())
        hass.services = FakeHass().services
        coordinator = ShadowCoordinator(hass, FakeEntry(), config, runtime)
        current = ready_inputs(cover_position=fresh(40), cover_motion=fresh("closing"))
        with patch(
            "custom_components.blind_control.coordinator.build_inputs_from_states",
            return_value=current,
        ):
            await coordinator.async_refresh()
        assert not runtime.override.active
        assert not runtime.override_tracker.initialized
        assert not hass.services.calls
        quiet = replace(current, cover_position=fresh(20), cover_motion=fresh("open"))
        with patch(
            "custom_components.blind_control.coordinator.build_inputs_from_states",
            return_value=quiet,
        ):
            with patch(
                "custom_components.blind_control.coordinator.time.monotonic", return_value=100
            ):
                await coordinator.async_refresh()
            with patch(
                "custom_components.blind_control.coordinator.time.monotonic", return_value=103
            ):
                await coordinator.async_refresh()
        assert runtime.override_tracker.baseline == 20
        assert not runtime.override.active
        assert len(hass.services.calls) == 1

    asyncio.run(scenario())


def test_invalidated_tv_intent_is_not_replayed_after_cooldown():
    runtime = ShadowRuntime(config_for("live", "blind_control"))
    runtime.on_restart(100)
    runtime.cooldown_tracker.record_write(100, now=0, cooldown_seconds=60)
    tv = runtime.evaluate(
        ready_inputs(activity_state=fresh("tv"), cover_position=fresh(100)), now=10
    )
    assert tv.trace.apply.cooldown_pending_target == 60
    neutral = ready_inputs(
        day_state=fresh("evening"), sun_azimuth=fresh(304), cover_position=fresh(100)
    )
    runtime.evaluate(neutral, now=20)
    assert runtime.cooldown_tracker.pending_target is None
    after = runtime.evaluate(neutral, now=70)
    assert after.trace.apply.approved_target is None
    pc = runtime.evaluate(
        ready_inputs(activity_state=fresh("pc"), cover_position=fresh(100)), now=71
    )
    assert pc.trace.apply.approved_target == 75


def test_rename_is_explicit_binding_change_with_fresh_baseline_and_exact_restore():
    now = datetime.now(UTC)
    original = config_for("shadow", "legacy").to_mapping()
    renamed = {**original, "input_bindings": {"cover_position": "cover.renamed_fixture"}}
    new_config = BlindControlConfig.from_mapping(renamed)
    states = {
        "cover.renamed_fixture": FakeState(
            "open", attributes={"current_position": 42}, updated_at=now
        )
    }
    assert not build_inputs_from_states(
        states, BlindControlConfig.from_mapping(original), now=now
    ).cover_position.usable
    new_inputs = build_inputs_from_states(states, new_config, now=now)
    assert new_inputs.cover_position.value == 42
    runtime = ShadowRuntime(new_config)
    runtime.on_restart(None)
    runtime.observe_cover_position(42, now=1)
    runtime.observe_cover_position(42, now=3)
    assert not runtime.override.active
    assert runtime.override_tracker.baseline == 42
    assert BlindControlConfig.from_mapping(original).to_mapping() == original


def test_waking_does_not_locally_suppress_canonical_private_time():
    trace = DecisionEngine().evaluate(
        ready_inputs(bio_state=fresh("waking"), private_time=fresh(True))
    )
    candidate = next(c for c in trace.candidates if c.key == "private_time")
    assert candidate.active
    assert not candidate.paused


def test_cloud_threshold_is_percent_not_a_fraction():
    engine = DecisionEngine()
    states = []
    for cloud in (0, 75, 100):
        trace = engine.evaluate(ready_inputs(cloud_cover=fresh(cloud), outdoor_lux=fresh(12000)))
        states.append(trace.solar.state.value)
    assert states == ["direct_sun", "cloud_shadow", "cloud_shadow"]


def test_missing_evidence_interrupts_settling_and_zero_settle_is_rejected():
    runtime = ShadowRuntime()
    runtime.on_restart(50)
    runtime.begin_own_write(20, now=0)
    runtime.observe_cover_position(20, now=1)
    runtime.observe_cover_position(None, now=2)
    runtime.observe_cover_position(20, now=3)
    assert runtime.override_tracker.own_target == 20
    runtime.observe_cover_position(20, now=5)
    assert runtime.override_tracker.own_target is None
    with pytest.raises(ValueError):
        BlindControlConfig.from_mapping({"position_settle_seconds": 0})
    assert BlindControlConfig.from_mapping({"config_version": 6}).target("sleep") == 5
