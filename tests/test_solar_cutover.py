"""Solar classification must distinguish valid low energy from missing evidence."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from test_apply import FakeHass, config_for, fresh, ready_inputs
from test_coordinator import FakeState

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.contracts import InputObservation, InputQuality
from custom_components.blind_control.coordinator import build_inputs_from_states
from custom_components.blind_control.engine import DecisionEngine
from custom_components.blind_control.shadow import ShadowRuntime
from custom_components.blind_control.solar import calculate_solar_exposure
from custom_components.blind_control.ux_contract import build_ux_snapshot


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"sun_elevation": -2, "day_state": "late_night"}, "night"),
        ({"sun_azimuth": 304}, "solar_not_on_window"),
        ({}, "direct_sun"),
        ({"expected_direct_radiation": 0, "outdoor_lux": 3000}, "diffuse_bright"),
        ({"cloud_cover": 90}, "cloud_shadow"),
        (
            {
                "sun_elevation": 5.88,
                "sun_azimuth": 88.07,
                "outdoor_lux": 299,
                "expected_direct_radiation": 0,
                "expected_diffuse_radiation": 2.1,
            },
            "low_light",
        ),
    ],
)
def test_complete_solar_evidence_has_valid_classification(changes, expected):
    inputs = ready_inputs(**{key: fresh(value) for key, value in changes.items()})
    result = calculate_solar_exposure(inputs, BlindControlConfig.defaults())
    assert result.state.value == expected
    assert not result.quality_blockers
    assert not DecisionEngine().evaluate(inputs).failure.active


@pytest.mark.parametrize("key", ["sun_elevation", "sun_azimuth", "outdoor_lux"])
@pytest.mark.parametrize(
    "quality", [InputQuality.UNKNOWN, InputQuality.STALE, InputQuality.CONFLICT]
)
@pytest.mark.parametrize("elevation", [-2, 5.88])
def test_horizon_first_replaces_v063_global_mandatory_contract(key, quality, elevation):
    inputs = ready_inputs(sun_elevation=fresh(elevation), outdoor_lux=fresh(1))
    inputs = replace(inputs, **{key: InputObservation(quality=quality, reason="fixture_rejected")})
    result = calculate_solar_exposure(inputs, BlindControlConfig.defaults())
    if elevation <= 0 and key != "sun_elevation":
        assert result.state.value == "night"
        assert result.lifecycle == "INACTIVE"
        assert not result.quality_blockers
    else:
        assert result.state.value == "unknown"
        assert any(item.key == key for item in result.quality_blockers)
    assert not DecisionEngine().evaluate(inputs).failure.active
    sleep = DecisionEngine().evaluate(replace(inputs, bio_state=fresh("sleep")))
    assert sleep.effective_target == 5


def test_low_light_without_optional_model_is_valid_and_cold_remains_independent():
    inputs = ready_inputs(outdoor_lux=fresh(299), outdoor_temperature=fresh(5))
    inputs = replace(
        inputs,
        **{
            key: InputObservation()
            for key in (
                "expected_direct_radiation",
                "expected_diffuse_radiation",
                "cloud_cover",
                "lux_trend",
            )
        },
    )
    trace = DecisionEngine().evaluate(inputs)
    assert trace.solar.state.value == "low_light"
    assert not trace.failure.active
    assert next(item for item in trace.candidates if item.key == "cold_insulation").active


@pytest.mark.parametrize(
    "key,value",
    [
        ("sun_elevation", 91),
        ("sun_azimuth", -1),
        ("sun_azimuth", 361),
        ("outdoor_lux", -1),
        ("outdoor_lux", float("nan")),
        ("sun_elevation", True),
    ],
)
def test_implausible_mandatory_solar_values_remain_unknown(key, value):
    result = calculate_solar_exposure(
        ready_inputs(**{key: fresh(value)}), BlindControlConfig.defaults()
    )
    assert result.state.value == "unknown"
    assert result.quality_blockers[0].quality is InputQuality.CONFLICT


@pytest.mark.parametrize("mode", ["shadow", "live"])
@pytest.mark.parametrize("owner", ["legacy", "blind_control"])
@pytest.mark.parametrize("enabled", [False, True])
def test_low_light_obeys_all_writer_gates_and_projects_cutover_diagnostics(mode, owner, enabled):
    async def scenario():
        config = config_for(mode, owner, apply_enabled=enabled)
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        inputs = ready_inputs(outdoor_lux=fresh(299), expected_direct_radiation=fresh(0))
        snapshot = runtime.evaluate(inputs, now=20)
        ux = build_ux_snapshot(snapshot, config)
        assert ux["settings"]["apply_enabled"] == enabled
        assert ux["settings"]["runtime_mode"] == mode
        assert ux["settings"]["apply_owner"] == owner
        assert ux["overview"]["cover_position"] == 42
        assert ux["overview"]["baseline_position"] == 42
        assert ux["overview"]["baseline_ready"] is True
        assert ux["overview"]["technical"]["cover_ready"] is True
        assert ux["overview"]["technical"]["opening_state"] == "closed"
        assert ux["overview"]["technical"]["apply"]["reason"]
        hass = FakeHass()
        result = await CoverApplyExecutor(hass, config, runtime).async_apply(snapshot, now=20)
        expected = mode == "live" and owner == "blind_control" and enabled
        assert result.actuation_executed == expected
        assert len(hass.services.calls) == int(expected)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "key,value,floor",
    [
        ("outdoor_lux", 299, 900),
        ("sun_elevation", 5.88, 900),
        ("sun_azimuth", 88.07, 900),
        ("indoor_temperature", 22, 1800),
        ("outdoor_temperature", 12, 1800),
        ("cloud_cover", 0, 1800),
        ("expected_direct_radiation", 0, 1200),
        ("expected_diffuse_radiation", 2.1, 1200),
    ],
)
def test_telemetry_old_binding_floor_and_real_expiry(key, value, floor):
    config = BlindControlConfig.from_mapping(
        {
            "observation_freshness_seconds": 120,
            "input_bindings": {key: "sensor.fixture"},
            "binding_freshness": {key: {"max_age_seconds": 120}},
        }
    )
    now = datetime.now(UTC)
    for age, usable in ((600, True), (floor + 1, False)):
        state = FakeState(
            str(value), entity_id="sensor.fixture", updated_at=now - timedelta(seconds=age)
        )
        result = getattr(build_inputs_from_states({"sensor.fixture": state}, config, now=now), key)
        assert result.usable == usable
    state.attributes["quality"] = "conflict"
    state.last_updated = now
    assert not getattr(
        build_inputs_from_states({"sensor.fixture": state}, config, now=now), key
    ).usable
