"""Issue #3: real repros and independent dimensional/race invariants."""

import asyncio
import importlib
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from test_apply import FakeHass, config_for, fresh, ready_inputs
from test_bootstrap import (
    _FakeConfigEntry,
    _FakeConnection,
    _FakeHomeAssistant,
    _home_assistant_imports,
)
from test_coordinator import FakeState

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.contracts import InputObservation, InputQuality
from custom_components.blind_control.coordinator import build_inputs_from_states
from custom_components.blind_control.engine import DecisionEngine
from custom_components.blind_control.shadow import ShadowRuntime


@pytest.mark.parametrize(
    "key", ["outdoor_lux", "sun_azimuth", "expected_direct_radiation", "cloud_cover", "lux_trend"]
)
@pytest.mark.parametrize(
    "quality", [InputQuality.STALE, InputQuality.UNAVAILABLE, InputQuality.CONFLICT]
)
def test_night_is_independent_of_exposure_quality(key, quality):
    inputs = ready_inputs(
        bio_state=fresh("sleep"),
        sun_elevation=fresh(-2),
        **{key: InputObservation(quality=quality, reason="fixture_loss")},
    )
    trace = DecisionEngine().evaluate(inputs)
    assert trace.solar.lifecycle == "INACTIVE"
    assert trace.solar.state.value == "night"
    assert trace.effective_target == 5
    assert not trace.failure.active


@pytest.mark.parametrize("lux", [2, 100000])
def test_night_horizon_precedes_lux(lux):
    trace = DecisionEngine().evaluate(ready_inputs(sun_elevation=fresh(-2), outdoor_lux=fresh(lux)))
    assert trace.solar.lifecycle == "INACTIVE" and trace.solar.state.value == "night"


@pytest.mark.parametrize(
    "quality", [InputQuality.FRESH, InputQuality.STALE, InputQuality.UNAVAILABLE]
)
def test_day_low_light_is_active_even_when_exposure_unknown(quality):
    trace = DecisionEngine().evaluate(
        ready_inputs(outdoor_lux=InputObservation(value=2, quality=quality))
    )
    assert trace.solar.lifecycle == "ACTIVE"
    assert trace.solar.state.value == ("low_light" if quality == InputQuality.FRESH else "unknown")


@pytest.mark.parametrize(
    "quality", [InputQuality.UNKNOWN, InputQuality.UNAVAILABLE, InputQuality.CONFLICT]
)
def test_unknown_sun_cannot_fall_back_to_old_elevation(quality):
    trace = DecisionEngine().evaluate(
        ready_inputs(sun_horizon=InputObservation(source="owner", quality=quality))
    )
    assert trace.solar.lifecycle == "UNKNOWN"


def test_stateful_sun_horizon_survives_geometry_ttl_without_removing_day_checks():
    now = datetime.now(UTC)
    config = BlindControlConfig.from_mapping(
        {
            "input_bindings": {
                "sun_elevation": "sun.fixture",
                "sun_azimuth": "sun.fixture",
            }
        }
    )
    state = FakeState(
        "below_horizon",
        entity_id="sun.fixture",
        attributes={"elevation": -2, "azimuth": 50},
        updated_at=now - timedelta(minutes=20),
    )
    inputs = build_inputs_from_states({"sun.fixture": state}, config, now=now)
    assert not inputs.sun_elevation.usable
    assert inputs.sun_horizon.usable
    assert DecisionEngine().evaluate(inputs).solar.lifecycle == "INACTIVE"
    state.state = "above_horizon"
    state.attributes["elevation"] = 2
    trace = DecisionEngine().evaluate(
        build_inputs_from_states({"sun.fixture": state}, config, now=now)
    )
    assert trace.solar.lifecycle == "ACTIVE" and trace.solar.state.value == "unknown"


@pytest.mark.parametrize(
    "attributes,expected",
    [
        (
            {
                "media_device": "pc",
                "gaming_platform": "pc",
                "pc_active": True,
                "entertainment_active": True,
            },
            "pc",
        ),
        ({"media_device": "pc", "entertainment_active": True}, "pc"),
        ({"gaming_platform": "pc", "entertainment_active": True}, "pc"),
        ({"media_device": "tv"}, "tv"),
        ({"media_activity_context": "streaming"}, "tv"),
        ({"gaming_platform": "ps5"}, "tv"),
        ({"gaming_platform": "xbox"}, "tv"),
        ({"gaming_platform": "switch"}, "tv"),
    ],
)
def test_canonical_screen_specificity(attributes, expected):
    config = BlindControlConfig.from_mapping(
        {"input_bindings": {"activity_state": "sensor.fixture"}}
    )
    observation = build_inputs_from_states(
        {"sensor.fixture": FakeState("gaming", attributes=attributes)}, config
    ).activity_state
    assert observation.usable and observation.value == expected
    assert dict(observation.evidence)["activity_state"] == "gaming"
    for key in ("media_device", "gaming_platform"):
        if key in attributes:
            assert dict(observation.evidence)[key] == attributes[key]
    trace = DecisionEngine().evaluate(ready_inputs(activity_state=observation))
    assert trace.effective_target == (75 if expected == "pc" else 60)


def test_conflicting_specific_screen_evidence_is_feature_local():
    config = BlindControlConfig.from_mapping(
        {"input_bindings": {"activity_state": "sensor.fixture"}}
    )
    observation = build_inputs_from_states(
        {
            "sensor.fixture": FakeState(
                "gaming", attributes={"media_device": "tv", "gaming_platform": "pc"}
            )
        },
        config,
    ).activity_state
    assert observation.quality == InputQuality.CONFLICT
    trace = DecisionEngine().evaluate(
        ready_inputs(activity_state=observation, bio_state=fresh("sleep"))
    )
    assert trace.effective_target == 5
    assert any(issue.feature == "glare" for issue in trace.decision.issues)


@pytest.mark.parametrize(
    "context,bad_key",
    [("sleep", "outdoor_lux"), ("away", "outdoor_temperature"), ("privacy", "sun_azimuth")],
)
def test_independent_closers_survive_feature_loss(context, bad_key):
    config = BlindControlConfig.defaults()
    changes = {bad_key: InputObservation(quality=InputQuality.UNAVAILABLE)}
    changes["bio_state" if context == "sleep" else context] = fresh(
        "sleep" if context == "sleep" else True
    )
    trace = DecisionEngine(config).evaluate(ready_inputs(cover_position=fresh(100), **changes))
    assert trace.effective_target == config.target(context)
    assert not trace.failure.active


@pytest.mark.parametrize("bio,target", [("sleep", 5), ("provisional_sleep", 5), ("waking", 100)])
def test_context_clamp_and_waking_pause(bio, target):
    trace = DecisionEngine().evaluate(
        ready_inputs(bio_state=fresh(bio), activity_state=fresh("tv"))
    )
    assert trace.effective_target == target
    glare = next(item for item in trace.decision.contributions if item.variant == "tv")
    assert glare.status == ("paused" if bio == "waking" else "active")


def test_daylight_mismatch_does_not_delay_waking_or_private_time():
    inputs = ready_inputs(sun_elevation=fresh(-2))
    assert DecisionEngine().evaluate(inputs).effective_target is None
    waking = DecisionEngine().evaluate(replace(inputs, bio_state=fresh("waking")))
    assert waking.effective_target == 100
    private = DecisionEngine().evaluate(
        replace(inputs, bio_state=fresh("waking"), private_time=fresh(True))
    )
    assert private.effective_target == BlindControlConfig.defaults().target("private_time")
    assert any(
        item.feature == "private_time" and item.status == "active"
        for item in private.decision.contributions
    )


def test_heat_and_glare_remain_visible_and_safety_overrules_soft_constraints():
    inputs = ready_inputs(outdoor_temperature=fresh(34), activity_state=fresh("pc"))
    trace = DecisionEngine().evaluate(inputs)
    assert trace.effective_target == 15
    assert {item.feature for item in trace.decision.contributions if item.status == "active"} >= {
        "heat",
        "glare",
    }
    safety = DecisionEngine().evaluate(
        replace(
            inputs, bio_state=fresh("sleep"), opening_state=fresh("open"), cover_position=fresh(30)
        )
    )
    assert safety.effective_target >= 30
    assert safety.decision.safety.min_open >= 30
    assert any(item.status == "suppressed" for item in safety.decision.contributions)


@pytest.mark.parametrize(
    "gate", ["automation", "apply", "owner", "newer", "manual", "stop", "safety"]
)
def test_old_lease_never_dispatches_after_invalidation(gate):
    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        old = runtime.evaluate(ready_inputs(), now=1)
        if gate in {"automation", "apply", "owner"}:
            changes = (
                {"automation_enabled": False}
                if gate == "automation"
                else {"apply_enabled": False}
                if gate == "apply"
                else {"apply_owner": "legacy"}
            )
            runtime.update_config(replace(config, **changes), ready_inputs(), now=2)
        elif gate == "newer":
            runtime.evaluate(ready_inputs(bio_state=fresh("sleep")), now=2)
        elif gate == "manual":
            runtime.observe_cover_position(70, now=2, moving=True)
        elif gate == "safety":
            runtime.evaluate(ready_inputs(opening_state=fresh("open")), now=2)
        else:
            runtime.stop()
        hass = FakeHass()
        await CoverApplyExecutor(hass, config, runtime).async_apply(old, now=3)
        assert not hass.services.calls

    asyncio.run(scenario())


@pytest.mark.parametrize("path", ["panel", "operation", "native", "listener", "unload"])
def test_config_mutation_revokes_before_any_reload_await(path):
    with _home_assistant_imports():
        integration = importlib.import_module("custom_components.blind_control")
        transport = importlib.import_module("custom_components.blind_control.websocket_api")
        config_flow = importlib.import_module("custom_components.blind_control.config_flow")

        async def scenario():
            config = config_for("live", "blind_control")
            hass = _FakeHomeAssistant()
            entry = _FakeConfigEntry("dimensions", data=config.to_mapping())
            await integration.async_setup(hass, {})
            await integration.async_setup_entry(hass, entry)
            runtime = entry.runtime_data.shadow
            runtime.on_restart(42)
            snapshot = runtime.evaluate(ready_inputs(), now=1)
            hass.config_entries.async_entries = lambda domain: (
                [entry] if domain == "blind_control" else []
            )
            if path == "panel":
                handler = next(
                    item
                    for item in sys.modules["homeassistant.components.websocket_api"].commands
                    if item.websocket_schema["type"] == transport.UPDATE_OPTIONS
                )
                connection = _FakeConnection(is_admin=True)
                await handler(hass, connection, {"id": 1, "options": {"automation_enabled": False}})
                assert not connection.errors
            elif path == "operation":
                from custom_components.blind_control.operation import revision

                handler = next(
                    item
                    for item in sys.modules["homeassistant.components.websocket_api"].commands
                    if item.websocket_schema["type"] == transport.SET_OPERATION
                )
                connection = _FakeConnection(is_admin=True)
                await handler(
                    hass,
                    connection,
                    {
                        "id": 2,
                        "expected_revision": revision(config),
                        "operation": {
                            "runtime_mode": "live",
                            "apply_owner": "blind_control",
                            "apply_enabled": False,
                        },
                    },
                )
                assert not connection.errors
            elif path == "native":
                flow = config_flow.BlindControlOptionsFlow(entry)
                result = await flow.async_step_init({"automation_enabled": False})
                assert result["type"] == "create_entry"
            else:

                async def boundary(*_args):
                    assert not runtime.active
                    assert runtime.latest_snapshot is None
                    return True

                if path == "listener":
                    hass.config_entries.async_reload = boundary
                    await integration._async_options_updated(hass, entry)
                else:
                    hass.config_entries.async_unload_platforms = boundary
                    await integration.async_unload_entry(hass, entry)
            assert not runtime.active
            writer_hass = FakeHass()
            await CoverApplyExecutor(writer_hass, config, runtime).async_apply(snapshot)
            assert not writer_hass.services.calls

        asyncio.run(scenario())


def test_persisted_revision_change_blocks_before_async_listener_runs():
    from types import SimpleNamespace

    async def scenario():
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        snapshot = runtime.evaluate(ready_inputs(), now=1)
        entry = SimpleNamespace(data=config.to_mapping(), options={"automation_enabled": False})
        hass = FakeHass()
        await CoverApplyExecutor(hass, config, runtime, entry).async_apply(snapshot)
        assert not hass.services.calls

    asyncio.run(scenario())


def test_quality_loss_guard_allows_stronger_close_and_recovers_current_variant():
    runtime = ShadowRuntime()
    pc = ready_inputs(activity_state=fresh("pc"), cover_position=fresh(75))
    runtime.evaluate(pc, now=0)
    runtime.evaluate(pc, now=10)
    bad = replace(pc, outdoor_lux=InputObservation(quality=InputQuality.UNAVAILABLE))
    held = runtime.evaluate(bad, now=15)
    assert held.effective_target <= 75
    closing = runtime.evaluate(replace(bad, bio_state=fresh("sleep")), now=20)
    assert closing.effective_target == 5
    tv = runtime.evaluate(replace(pc, activity_state=fresh("tv")), now=25)
    assert tv.effective_target == 60
    assert not any(
        item.variant == "pc" and item.status == "active" for item in tv.trace.decision.contributions
    )


def test_cool_air_cannot_open_through_privacy_and_storm_cannot_open_through_glare():
    engine = DecisionEngine()
    privacy = engine.evaluate(
        ready_inputs(
            privacy=fresh(True),
            air_movement=fresh(True),
            indoor_temperature=fresh(28),
            outdoor_temperature=fresh(18),
        )
    )
    assert privacy.effective_target <= engine.config.target("privacy")
    storm = engine.evaluate(
        ready_inputs(
            activity_state=fresh("tv"),
            outdoor_temperature=fresh(34),
            weather_alert=fresh(True),
            precipitation_trend=fresh(1),
            wind_trend=fresh(1),
        )
    )
    assert storm.effective_target == 60


@pytest.mark.parametrize(
    "quality", [InputQuality.UNKNOWN, InputQuality.CONFLICT, InputQuality.STALE]
)
def test_unknown_opening_never_invents_safety_open(quality):
    trace = DecisionEngine().evaluate(
        ready_inputs(
            opening_state=InputObservation(value="open", quality=quality), bio_state=fresh("sleep")
        )
    )
    assert trace.safety.status == "blocked"
    assert trace.effective_target is None
    assert trace.decision.safety.block_direction == "both"


def test_sleep_5_is_clamped_to_custom_hard_safety_30():
    raw = BlindControlConfig.defaults().to_mapping()
    raw["profiles"]["window_safety"] = {"logical": 30}
    config = BlindControlConfig.from_mapping(raw)
    trace = DecisionEngine(config).evaluate(
        ready_inputs(bio_state=fresh("sleep"), opening_state=fresh("open"), cover_position=fresh(5))
    )
    assert trace.fachlicher_target == 5
    assert trace.effective_target == 30
    assert trace.decision.feasible_interval[0] == 30


@pytest.mark.parametrize("old,new,target", [("pc", "tv", 60), ("tv", "pc", 75)])
def test_cooldown_only_references_latest_screen_decision(old, new, target):
    config = config_for("live", "blind_control")
    runtime = ShadowRuntime(config)
    runtime.on_restart(42)
    runtime.evaluate(ready_inputs(activity_state=fresh(old)), now=0)
    old_snapshot = runtime.evaluate(ready_inputs(activity_state=fresh(old)), now=10)
    runtime.cooldown_tracker.record_write(
        old_snapshot.effective_target, now=10, cooldown_seconds=60
    )
    latest = runtime.evaluate(ready_inputs(activity_state=fresh(new)), now=11)
    assert latest.trace.apply.status == "cooldown"
    assert latest.effective_target == target
    assert runtime.cooldown_tracker.pending_target == target
    released = runtime.evaluate(ready_inputs(activity_state=fresh(new)), now=71)
    assert released.effective_target == target
    assert (
        released.trace.decision.decision_generation
        > old_snapshot.trace.decision.decision_generation
    )
    assert released.trace.apply.status == "live_ready"
