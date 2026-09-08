"""v0.6.2: reproduce A/B unchanged, correct only stationary cover evidence."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from test_apply import fresh, ready_inputs
from test_coordinator import FakeEntry, FakeHass, FakeState

from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.contracts import InputQuality, SolarExposureState
from custom_components.blind_control.coordinator import ShadowCoordinator, build_inputs_from_states
from custom_components.blind_control.shadow import ShadowRuntime


def cover_config(inverted=False):
    return BlindControlConfig.from_mapping(
        {
            "config_version": 6,
            "axis_inverted": inverted,
            "observation_freshness_seconds": 120,
            "binding_freshness": {
                "cover_position": {"max_age_seconds": 120, "require_timestamp": True}
            },
            "input_bindings": {
                "cover_position": "cover.fixture",
                "cover_available": "cover.fixture",
            },
        }
    )


def observe(
    state="open", position=100, *, attributes=None, age=28800, inverted=False, domain="cover"
):
    now = datetime.now(UTC)
    values = {"current_position": position} if position is not None else {}
    values.update(attributes or {})
    config = cover_config(inverted)
    cover = FakeState(
        state,
        attributes=values,
        updated_at=now - timedelta(seconds=age),
        entity_id=f"{domain}.fixture",
    )
    return build_inputs_from_states({"cover.fixture": cover}, config, now=now)


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"config_version": 6},
        {
            "config_version": 6,
            "binding_freshness": {
                "outdoor_temperature": {"max_age_seconds": 120, "require_timestamp": True}
            },
        },
    ],
)
def test_a_persisted_120_seconds_keeps_temperature_fresh_through_roundtrip(raw):
    config = BlindControlConfig.from_mapping(
        {
            **raw,
            "observation_freshness_seconds": 120,
            "input_bindings": {"outdoor_temperature": "weather.fixture"},
        }
    )
    now = datetime.now(UTC)
    state = FakeState(
        "cloudy",
        attributes={"temperature": 12},
        updated_at=now - timedelta(seconds=600),
        entity_id="weather.fixture",
    )
    for current in (
        config,
        BlindControlConfig.from_mapping(json.loads(json.dumps(config.to_mapping()))),
    ):
        result = build_inputs_from_states({"weather.fixture": state}, current, now=now)
        assert current.binding_policy("outdoor_temperature").max_age_seconds == 1800
        assert result.outdoor_temperature.usable and result.outdoor_temperature.value == 12


def test_b_low_light_known_geometry_is_expected_solar_unknown():
    result = ShadowRuntime().evaluate(
        ready_inputs(
            outdoor_lux=fresh(299),
            sun_elevation=fresh(5.88),
            sun_azimuth=fresh(88.07),
            expected_direct_radiation=fresh(0),
            expected_diffuse_radiation=fresh(2.1),
        ),
        now=0,
    )
    assert result.trace.solar.state is SolarExposureState.UNKNOWN
    assert result.trace.solar.reason == "insufficient_radiation_or_lux_evidence_with_known_geometry"
    assert "solar_aggregate_unknown" in [
        item.reason for item in result.trace.failure.quality_blockers
    ]
    assert not result.write_path_reachable


@pytest.mark.parametrize("state,position", [("open", 100), ("closed", 0), ("stopped", 42)])
@pytest.mark.parametrize("inverted", [False, True])
def test_c_old_stationary_cover_establishes_restart_baseline(state, position, inverted):
    async def scenario():
        config = cover_config(inverted)
        now = datetime.now(UTC)
        cover = FakeState(
            state,
            attributes={"current_position": position},
            updated_at=now - timedelta(hours=8),
            entity_id="cover.fixture",
        )
        runtime = ShadowRuntime(config)
        coordinator = ShadowCoordinator(
            FakeHass({"cover.fixture": cover}), FakeEntry(), config, runtime
        )
        with patch("custom_components.blind_control.coordinator.time.monotonic", return_value=0):
            first = await coordinator.async_refresh()
        with patch("custom_components.blind_control.coordinator.time.monotonic", return_value=3):
            final = await coordinator.async_refresh()
        assert first.inputs["cover_position"]["quality"] == "fresh"
        assert first.inputs["cover_motion"]["quality"] == "fresh"
        assert final.movement_status == "idle"
        assert runtime.override_tracker.baseline == (100 - position if inverted else position)
        assert runtime.override_tracker.initialized and not runtime.override.active
        assert not final.actuation_executed and not final.write_path_reachable

    asyncio.run(scenario())


@pytest.mark.parametrize("motion", ["opening", "closing"])
@pytest.mark.parametrize("inverted", [False, True])
def test_motion_is_semantic_but_old_moving_position_remains_stale(motion, inverted):
    result = observe(motion, 25, inverted=inverted)
    assert result.cover_motion.usable and result.cover_motion.value == motion
    assert result.cover_position.quality is InputQuality.STALE
    recent = observe(motion, 25, age=0, inverted=inverted)
    assert recent.cover_position.value == (75 if inverted else 25)
    assert recent.cover_motion.value == motion


@pytest.mark.parametrize(
    "key", ["device_timestamp", "source_timestamp", "measurement_timestamp", "observed_at"]
)
def test_explicit_device_timestamp_precedes_ha_state(key):
    now = datetime.now(UTC)
    fresh_result = observe(attributes={key: now})
    assert fresh_result.cover_position.usable
    assert fresh_result.cover_position.updated_at == now
    stale = observe(attributes={key: now - timedelta(seconds=600)}, age=0)
    assert stale.cover_position.quality is InputQuality.STALE


@pytest.mark.parametrize(
    "attributes,quality",
    [
        ({"restored": True}, InputQuality.DEGRADED),
        ({"quality": "conflict"}, InputQuality.CONFLICT),
        ({"source_quality": "stale"}, InputQuality.STALE),
        ({"device_timestamp": "invalid"}, InputQuality.DEGRADED),
        ({"device_timestamp": None}, InputQuality.DEGRADED),
        ({"device_timestamp": "2099-01-01T00:00:00+00:00"}, InputQuality.CONFLICT),
    ],
)
def test_negative_device_evidence_never_falls_back_to_stationary_state(attributes, quality):
    result = observe(attributes=attributes, age=0)
    assert result.cover_position.quality is quality
    assert not result.cover_position.usable


@pytest.mark.parametrize("state", ["unknown", "unavailable", "invalid"])
def test_bad_cover_state_is_unusable(state):
    result = observe(state, age=0)
    assert not result.cover_position.usable and not result.cover_motion.usable


@pytest.mark.parametrize("position", [None, "bad", -1, 101, True, float("nan")])
def test_bad_position_does_not_erase_valid_semantic_motion(position):
    result = observe(position=position, age=0)
    assert not result.cover_position.usable
    assert result.cover_motion.usable and result.cover_motion.value == "open"
    if position in (-1, 101):
        assert result.cover_position.quality is InputQuality.CONFLICT


def test_stationary_exception_does_not_apply_to_non_cover_binding():
    assert not observe(domain="sensor").cover_position.usable


def test_invalid_preferred_timestamp_cannot_fall_through_to_fresh_lower_precedence():
    result = observe(
        attributes={"device_timestamp": "invalid", "source_timestamp": datetime.now(UTC)}, age=0
    )
    assert not result.cover_position.usable and not result.cover_motion.usable


def test_position_quality_is_separate_from_motion_but_generic_device_quality_blocks_both():
    position_bad = observe(position=101, age=0)
    assert not position_bad.cover_position.usable
    assert position_bad.cover_motion.usable
    generic_bad = observe(attributes={"source_quality": "conflict"}, age=0)
    assert not generic_bad.cover_position.usable and not generic_bad.cover_motion.usable


def test_missing_position_keeps_runtime_unavailable_despite_known_motion():
    async def scenario():
        config = cover_config()
        state = FakeState("open", updated_at=datetime.now(UTC), entity_id="cover.fixture")
        runtime = ShadowRuntime(config)
        result = await ShadowCoordinator(
            FakeHass({"cover.fixture": state}), FakeEntry(), config, runtime
        ).async_refresh()
        assert result.movement_status == "position_unavailable"
        assert not runtime.override_tracker.initialized and not runtime.override.active

    asyncio.run(scenario())


@pytest.mark.parametrize("inverted", [False, True])
def test_opening_open_never_lowers_old_stationary_position(inverted):
    inputs = observe(position=40 if inverted else 60, inverted=inverted)
    runtime = ShadowRuntime(cover_config(inverted))
    result = runtime.evaluate(
        replace(
            ready_inputs(opening_state=fresh("open")),
            cover_position=inputs.cover_position,
            cover_motion=inputs.cover_motion,
        ),
        now=0,
    )
    assert result.trace.safety.approved_target >= 60
    assert result.effective_target >= 60
