from __future__ import annotations

import asyncio
import sys
import threading
import types
import unittest
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "blind_control"
if "custom_components.blind_control" not in sys.modules:
    package = types.ModuleType("custom_components.blind_control")
    package.__path__ = [str(PACKAGE)]
    sys.modules["custom_components.blind_control"] = package

from custom_components.blind_control.config import BlindControlConfig  # noqa: E402
from custom_components.blind_control.coordinator import (  # noqa: E402
    ShadowCoordinator,
    build_inputs_from_states,
    build_legacy_evidence_from_states,
)
from custom_components.blind_control.shadow import ShadowRuntime  # noqa: E402
from custom_components.blind_control.shadow_diff import DiffClassification  # noqa: E402


class FakeState:
    def __init__(self, state: str, *, attributes=None, updated_at=None, entity_id=None):
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}
        self.last_updated = updated_at


class FakeStates:
    def __init__(self, values):
        self.values = values

    def get(self, entity_id):
        return self.values.get(entity_id)


class FakeHass:
    def __init__(self, states):
        self.states = FakeStates(states)
        self.tasks = []
        self.jobs = []

    def add_job(self, callback):
        self.jobs.append(callback)
        callback()

    def async_create_task(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.append(task)
        return task


class ThreadAwareFakeHass(FakeHass):
    """Record the actual worker-to-HA-loop scheduling path."""

    def __init__(self, states, loop) -> None:
        super().__init__(states)
        self.loop = loop
        self.loop_thread_id = threading.get_ident()
        self.add_job_thread_ids: list[int] = []
        self.create_task_thread_ids: list[int] = []

    def add_job(self, callback) -> None:
        self.add_job_thread_ids.append(threading.get_ident())
        self.loop.call_soon_threadsafe(callback)

    def async_create_task(self, coroutine):
        self.create_task_thread_ids.append(threading.get_ident())
        if threading.get_ident() != self.loop_thread_id:
            coroutine.close()
            raise AssertionError("async_create_task escaped the Home Assistant event loop")
        return super().async_create_task(coroutine)


class FakeEntry:
    def __init__(self):
        self.runtime_data = None


class FakeEventRegistry:
    def __init__(self):
        self.state_callbacks = []
        self.time_callbacks = []
        self.intervals = []
        self.unsubscribed = 0

    def track_state_change(self, _hass, _entity_ids, callback):
        self.state_callbacks.append(callback)
        return self._unsubscribe

    def track_time_interval(self, _hass, callback, interval):
        self.time_callbacks.append(callback)
        self.intervals.append(interval)
        return self._unsubscribe

    def _unsubscribe(self):
        self.unsubscribed += 1


@contextmanager
def fake_home_assistant_event_modules():
    registry = FakeEventRegistry()
    homeassistant = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    event = types.ModuleType("homeassistant.helpers.event")
    event.async_track_state_change_event = registry.track_state_change
    event.async_track_time_interval = registry.track_time_interval
    helpers.event = event
    homeassistant.helpers = helpers
    with patch.dict(
        sys.modules,
        {
            "homeassistant": homeassistant,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.event": event,
        },
    ):
        yield registry


class CoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(UTC)
        self.config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {
                    "bio_state": "sensor.bio_state",
                    "activity_state": "sensor.activity_state",
                    "day_state": "sensor.day_state",
                    "day_context": "sensor.day_context",
                    "opening_state": "sensor.opening_state",
                    "opening_safe_for_blind": "binary_sensor.opening_safe",
                    "cover_available": "binary_sensor.cover_available",
                    "cover_ready": "binary_sensor.cover_ready",
                    "cover_position": "cover.observer",
                    "sun_elevation": "sensor.sun_geometry",
                    "sun_azimuth": "sensor.sun_geometry",
                    "outdoor_lux": "sensor.outdoor_lux",
                },
                "legacy_bindings": {
                    "active_mode": "sensor.legacy_mode",
                    "effective_target": "sensor.legacy_target",
                    "safety_status": "sensor.legacy_safety",
                    "apply_status": "sensor.legacy_apply",
                },
            }
        )
        self.states = {
            "sensor.bio_state": FakeState("awake", updated_at=self.now),
            "sensor.activity_state": FakeState("none", updated_at=self.now),
            "sensor.day_state": FakeState("forenoon", updated_at=self.now),
            "sensor.day_context": FakeState("weekday", updated_at=self.now),
            "sensor.opening_state": FakeState("closed", updated_at=self.now),
            "binary_sensor.opening_safe": FakeState("on", updated_at=self.now),
            "binary_sensor.cover_available": FakeState("on", updated_at=self.now),
            "binary_sensor.cover_ready": FakeState("on", updated_at=self.now),
            "cover.observer": FakeState(
                "closed",
                attributes={"current_position": 42, "device_timestamp": self.now},
                updated_at=self.now,
            ),
            "sensor.sun_geometry": FakeState(
                "on",
                attributes={"elevation": 30, "azimuth": 124},
                updated_at=self.now,
            ),
            "sensor.outdoor_lux": FakeState("12000", updated_at=self.now),
            "sensor.legacy_mode": FakeState("daylight", updated_at=self.now),
            "sensor.legacy_target": FakeState("100", updated_at=self.now),
            "sensor.legacy_safety": FakeState("ready", updated_at=self.now),
            "sensor.legacy_apply": FakeState("shadow_ready", updated_at=self.now),
        }

    def test_owner_bindings_create_fresh_inputs_and_legacy_evidence(self) -> None:
        inputs = build_inputs_from_states(self.states, self.config, now=self.now)
        legacy = build_legacy_evidence_from_states(self.states, self.config, now=self.now)

        self.assertEqual(inputs.bio_state.value, "awake")
        self.assertEqual(inputs.cover_position.value, 42.0)
        self.assertEqual(inputs.sun_elevation.value, 30.0)
        self.assertEqual(inputs.activity_state.value, "none")
        self.assertTrue(inputs.activity_state.usable)
        self.assertTrue(inputs.opening_state.usable)
        self.assertTrue(all(observation.usable for _, observation in legacy.observations))
        self.assertEqual(
            set(dict(legacy.observations)),
            {
                "active_mode",
                "effective_target",
                "safety_status",
                "apply_status",
            },
        )

    def test_presence_adapter_prefers_away_gate_and_preserves_polarity(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"away": "sensor.owner_presence"}}
        )
        cases = (
            (FakeState("zuhause", attributes={"away_gate": False}), False),
            (FakeState("zuhause"), False),
            (FakeState("home"), False),
            (FakeState("abwesend"), True),
            (FakeState("not_home"), True),
            (FakeState("on"), True),
            (FakeState("off"), False),
        )

        for state, expected in cases:
            with self.subTest(state=state.state, expected=expected):
                observation = build_inputs_from_states(
                    {"sensor.owner_presence": state}, config, now=self.now
                ).away
                self.assertTrue(observation.usable)
                self.assertIs(observation.value, expected)

        degraded = build_inputs_from_states(
            {"sensor.owner_presence": FakeState("maybe")}, config, now=self.now
        ).away
        self.assertEqual(degraded.quality.value, "degraded")
        self.assertIsNone(degraded.value)

    def test_activity_adapter_uses_documented_state_and_attribute_evidence(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"activity_state": "sensor.owner_activity"}}
        )
        cases = (
            (FakeState("music", attributes={"pc_active": True}), "pc"),
            (FakeState("gaming", attributes={"gaming_platform": "ps5"}), "tv"),
            (FakeState("entertainment"), "tv"),
            (FakeState("music"), "none"),
            (
                FakeState(
                    "music",
                    attributes={"pc_active": True, "entertainment_active": True},
                ),
                "tv",
            ),
        )

        for state, expected in cases:
            with self.subTest(state=state.state, expected=expected):
                observation = build_inputs_from_states(
                    {"sensor.owner_activity": state}, config, now=self.now
                ).activity_state
                self.assertTrue(observation.usable)
                self.assertEqual(observation.value, expected)
                self.assertIn("core_state_glare_adapter", observation.reason)

        conflict = build_inputs_from_states(
            {
                "sensor.owner_activity": FakeState(
                    "music",
                    attributes={"pc_active": True, "quality_status": "conflict"},
                )
            },
            config,
            now=self.now,
        ).activity_state
        self.assertEqual(conflict.quality.value, "conflict")
        self.assertIsNone(conflict.value)

    def test_private_time_day_context_and_master_attributes_are_field_specific(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {
                    "private_time": "sensor.owner_activity",
                    "day_context": "sensor.owner_day_context",
                    "privacy": "sensor.owner_privacy",
                    "indoor_temperature": "sensor.owner_indoor",
                    "outdoor_temperature": "sensor.owner_weather",
                    "cloud_cover": "sensor.owner_weather",
                }
            }
        )
        states = {
            "sensor.owner_activity": FakeState("music", attributes={"private": False}),
            "sensor.owner_day_context": FakeState("werktag"),
            "sensor.owner_privacy": FakeState("ready", attributes={"privacy_candidate": True}),
            "sensor.owner_indoor": FakeState("ready", attributes={"temperature": 23.4}),
            "sensor.owner_weather": FakeState(
                "ready",
                attributes={"outdoor_temperature": 14.2, "cloud_coverage": 56},
                updated_at=self.now,
            ),
        }

        inputs = build_inputs_from_states(states, config, now=self.now)

        self.assertFalse(inputs.private_time.value)
        self.assertEqual(inputs.day_context.value, "weekday")
        self.assertTrue(inputs.privacy.value)
        self.assertEqual(inputs.indoor_temperature.value, 23.4)
        self.assertEqual(inputs.outdoor_temperature.value, 14.2)
        self.assertEqual(inputs.cloud_cover.value, 56.0)

    def test_open_meteo_current_radiation_fields_remain_distinct_numeric_evidence(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {
                    "expected_direct_radiation": "sensor.contract_dni",
                    "expected_diffuse_radiation": "sensor.contract_diffuse",
                }
            }
        )
        inputs = build_inputs_from_states(
            {
                "sensor.contract_dni": FakeState("310", updated_at=self.now),
                "sensor.contract_diffuse": FakeState("95", updated_at=self.now),
            },
            config,
            now=self.now,
        )

        self.assertEqual(inputs.expected_direct_radiation.value, 310.0)
        self.assertEqual(inputs.expected_diffuse_radiation.value, 95.0)
        self.assertNotEqual(
            inputs.expected_direct_radiation.source,
            inputs.expected_diffuse_radiation.source,
        )

    def test_one_legacy_debug_contract_projects_all_comparison_fields(self) -> None:
        binding = "sensor.contract_legacy_debug"
        config = BlindControlConfig.from_mapping(
            {
                "legacy_bindings": {
                    key: binding
                    for key in ("active_mode", "effective_target", "safety_status", "apply_status")
                }
            }
        )
        legacy = build_legacy_evidence_from_states(
            {
                binding: FakeState(
                    "shadow",
                    attributes={
                        "active_mode": "heat",
                        "active_position": 15,
                        "apply_enabled": True,
                        "blockers": [],
                    },
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        )
        observations = dict(legacy.observations)

        self.assertEqual(observations["active_mode"].value, "heat")
        self.assertEqual(observations["effective_target"].value, 15.0)
        self.assertEqual(observations["safety_status"].value, "ready")
        self.assertEqual(observations["apply_status"].value, "ready")

    def test_every_canonical_day_phase_is_preserved(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"day_state": "sensor.owner_day"}}
        )
        phases = (
            "early_night",
            "late_night",
            "early_morning",
            "forenoon",
            "midday",
            "afternoon",
            "late_afternoon",
            "evening",
            "late_evening",
        )

        for phase in phases:
            with self.subTest(phase=phase):
                observation = build_inputs_from_states(
                    {"sensor.owner_day": FakeState(phase)}, config, now=self.now
                ).day_state
                self.assertTrue(observation.usable)
                self.assertEqual(observation.value, phase)

    def test_opening_polarity_cover_availability_and_standard_position_contracts(self) -> None:
        bindings = {
            "opening_safe_for_blind": "binary_sensor.owner_opening_safety",
            "cover_available": "cover.owner_cover",
            "cover_position": "cover.owner_cover",
        }
        state = FakeState(
            "closed",
            attributes={"current_position": 42},
            updated_at=self.now,
        )
        positive = BlindControlConfig.from_mapping(
            {
                "input_bindings": bindings,
                "opening_safety_polarity": "positive_safe",
            }
        )
        negative = BlindControlConfig.from_mapping(
            {
                "input_bindings": bindings,
                "opening_safety_polarity": "negative_unsafe",
            }
        )
        states = {
            "binary_sensor.owner_opening_safety": FakeState("on", updated_at=self.now),
            "cover.owner_cover": state,
        }

        positive_inputs = build_inputs_from_states(states, positive, now=self.now)
        negative_inputs = build_inputs_from_states(states, negative, now=self.now)
        unspecified_inputs = build_inputs_from_states(
            states,
            BlindControlConfig.from_mapping({"input_bindings": bindings}),
            now=self.now,
        )

        self.assertTrue(positive_inputs.opening_safe_for_blind.value)
        self.assertFalse(negative_inputs.opening_safe_for_blind.value)
        self.assertEqual(unspecified_inputs.opening_safe_for_blind.quality.value, "degraded")
        self.assertTrue(positive_inputs.cover_available.value)
        self.assertEqual(positive_inputs.cover_position.value, 42.0)
        self.assertTrue(positive_inputs.cover_position.usable)
        self.assertIn("standard_cover_ha_timestamp_contract", positive_inputs.cover_position.reason)

        restored = build_inputs_from_states(
            {
                **states,
                "cover.owner_cover": FakeState(
                    "closed",
                    attributes={"current_position": 42, "restored": True},
                    updated_at=self.now,
                ),
            },
            positive,
            now=self.now,
        ).cover_position
        self.assertEqual(restored.quality.value, "degraded")
        self.assertIsNone(restored.value)

    def test_stateful_owner_observation_is_not_staled_by_age_alone(self) -> None:
        old = self.now - timedelta(
            seconds=BlindControlConfig.defaults().observation_freshness_seconds + 1
        )
        states = {**self.states, "sensor.opening_state": FakeState("closed", updated_at=old)}
        inputs = build_inputs_from_states(states, self.config, now=self.now)

        self.assertTrue(inputs.opening_state.usable)
        self.assertTrue(inputs.opening_state.reason.endswith("stateful_contract_not_age_limited"))

    def test_time_critical_cover_observation_requires_timestamp_and_freshness(self) -> None:
        old = self.now - timedelta(
            seconds=BlindControlConfig.defaults().observation_freshness_seconds + 1
        )
        old_states = {
            **self.states,
            "cover.observer": FakeState(
                "closed",
                attributes={"current_position": 42, "device_timestamp": old},
                updated_at=self.now,
            ),
        }
        stale_inputs = build_inputs_from_states(old_states, self.config, now=self.now)
        missing_timestamp = {
            **self.states,
            "cover.observer": FakeState("closed", attributes={"current_position": 42}),
        }
        missing_inputs = build_inputs_from_states(missing_timestamp, self.config, now=self.now)

        self.assertFalse(stale_inputs.cover_position.usable)
        self.assertTrue(
            stale_inputs.cover_position.reason.endswith(
                "bound_entity_state_exceeded_freshness_window"
            )
        )
        self.assertFalse(missing_inputs.cover_position.usable)
        self.assertTrue(missing_inputs.cover_position.reason.endswith("required_timestamp_missing"))

    def test_cover_freshness_uses_device_timestamp_not_ha_state_time(self) -> None:
        old_device_timestamp = self.now - timedelta(
            seconds=self.config.observation_freshness_seconds + 1
        )
        device_state = FakeState(
            "closed",
            attributes={"current_position": 42, "device_timestamp": old_device_timestamp},
            updated_at=self.now,
        )
        inputs = build_inputs_from_states(
            {**self.states, "cover.observer": device_state}, self.config, now=self.now
        )

        self.assertFalse(inputs.cover_position.usable)
        self.assertTrue(
            inputs.cover_position.reason.endswith("bound_entity_state_exceeded_freshness_window")
        )
        self.assertEqual(inputs.cover_position.updated_at, old_device_timestamp)

        source_now = FakeState(
            "closed",
            attributes={"current_position": 42, "device_timestamp": self.now},
            updated_at=old_device_timestamp,
        )
        fresh_inputs = build_inputs_from_states(
            {**self.states, "cover.observer": source_now}, self.config, now=self.now
        )
        self.assertTrue(fresh_inputs.cover_position.usable)
        self.assertEqual(fresh_inputs.cover_position.updated_at, self.now)

    def test_freshness_contract_is_owner_and_field_specific(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {"outdoor_lux": "sensor.outdoor_lux"},
                "binding_freshness": {
                    "bio_state": {
                        "max_age_seconds": 1,
                        "require_timestamp": True,
                        "owner": "test_bio_owner",
                    }
                },
            }
        )

        self.assertEqual(config.binding_policy("bio_state").owner, "test_bio_owner")
        self.assertEqual(config.binding_policy("bio_state").max_age_seconds, 1)
        self.assertEqual(config.binding_policy("activity_state").owner, "core_state")
        self.assertIsNone(config.binding_policy("activity_state").max_age_seconds)
        self.assertEqual(config.binding_policy("cover_position").owner, "cover_device")
        self.assertEqual(config.binding_policy("cover_position").max_age_seconds, 120)
        self.assertEqual(config.binding_policy("outdoor_lux").max_age_seconds, 900)
        self.assertEqual(config.binding_policy("expected_direct_radiation").max_age_seconds, 1200)
        self.assertEqual(config.binding_policy("outdoor_temperature").max_age_seconds, 1800)

    def test_legacy_freshness_values_cannot_lower_field_safety_floors(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "observation_freshness_seconds": 120,
                "binding_freshness": {
                    key: {"max_age_seconds": 120, "require_timestamp": True}
                    for key in (
                        "outdoor_lux",
                        "sun_elevation",
                        "sun_azimuth",
                        "indoor_temperature",
                        "outdoor_temperature",
                    )
                },
            }
        )

        self.assertEqual(config.binding_policy("outdoor_lux").max_age_seconds, 900)
        self.assertEqual(config.binding_policy("sun_elevation").max_age_seconds, 900)
        self.assertEqual(config.binding_policy("sun_azimuth").max_age_seconds, 900)
        self.assertEqual(config.binding_policy("indoor_temperature").max_age_seconds, 1800)
        self.assertEqual(config.binding_policy("outdoor_temperature").max_age_seconds, 1800)

    def test_sun_observation_between_legacy_age_and_solar_floor_is_fresh(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "observation_freshness_seconds": 120,
                "input_bindings": {"sun_elevation": "sensor.sun"},
                "binding_freshness": {
                    "sun_elevation": {"max_age_seconds": 120, "require_timestamp": True}
                },
            }
        )
        observed_at = self.now - timedelta(seconds=600)
        observation = build_inputs_from_states(
            {"sensor.sun": FakeState("30", updated_at=observed_at)},
            config,
            now=self.now,
        ).sun_elevation

        self.assertTrue(observation.usable)
        self.assertEqual(observation.quality.value, "fresh")

    def test_stable_owner_quality_overrides_age_for_environment_measurement(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"indoor_temperature": "sensor.indoor"}}
        )
        old = self.now - timedelta(seconds=7200)
        observation = build_inputs_from_states(
            {
                "sensor.indoor": FakeState(
                    "23.4",
                    attributes={"source_quality": "healthy"},
                    updated_at=old,
                )
            },
            config,
            now=self.now,
        ).indoor_temperature

        self.assertTrue(observation.usable)
        self.assertEqual(observation.quality.value, "fresh")
        self.assertIn("owner_contract_quality_fresh_overrides_stable_ha_age", observation.reason)

    def test_weather_entity_temperature_attribute_is_a_numeric_outdoor_contract(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"outdoor_temperature": "weather.home"}}
        )
        observation = build_inputs_from_states(
            {
                "weather.home": FakeState(
                    "sunny",
                    attributes={"temperature": 14.2},
                    updated_at=self.now,
                    entity_id="weather.home",
                )
            },
            config,
            now=self.now,
        ).outdoor_temperature

        self.assertTrue(observation.usable)
        self.assertEqual(observation.value, 14.2)

    def test_activity_quality_uses_fresh_winner_not_irrelevant_stale_candidate(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"activity_state": "sensor.activity"}}
        )
        observation = build_inputs_from_states(
            {
                "sensor.activity": FakeState(
                    "music",
                    attributes={
                        "pc_active": True,
                        "activity_decision": {
                            "winner": "pc_active",
                            "input_sources": {
                                "pc_active": ["sensor.pc"],
                                "music": ["sensor.music"],
                            },
                            "freshness": {
                                "sensor.pc": {"status": "fresh"},
                                "sensor.music": {"status": "stale"},
                            },
                        },
                    },
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        ).activity_state

        self.assertTrue(observation.usable)
        self.assertEqual(observation.value, "pc")
        self.assertEqual(observation.quality.value, "fresh")

    def test_stale_private_time_never_becomes_false(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"private_time": "sensor.activity"}}
        )
        observation = build_inputs_from_states(
            {
                "sensor.activity": FakeState(
                    "private_time",
                    attributes={"private": True, "quality_status": "stale"},
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        ).private_time

        self.assertFalse(observation.usable)
        self.assertIsNone(observation.value)
        self.assertEqual(observation.quality.value, "stale")

    def test_cover_ready_ignores_unrelated_weather_degraded_marker(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"cover_ready": "binary_sensor.ready"}}
        )
        observation = build_inputs_from_states(
            {
                "binary_sensor.ready": FakeState(
                    "on",
                    attributes={
                        "cover_available": True,
                        "current_position": 42,
                        "policy_context_ready": True,
                        "quality_status": "weather_contract_degraded",
                    },
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        ).cover_ready

        self.assertTrue(observation.usable)
        self.assertTrue(observation.value)

    def test_owner_published_quality_is_not_hidden_by_a_recent_ha_timestamp(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"outdoor_temperature": "sensor.owner_weather"}}
        )
        degraded = build_inputs_from_states(
            {
                "sensor.owner_weather": FakeState(
                    "ready",
                    attributes={
                        "outdoor_temperature": 14.2,
                        "source_quality": "degraded",
                    },
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        ).outdoor_temperature
        stale = build_inputs_from_states(
            {
                "sensor.owner_weather": FakeState(
                    "14.2",
                    attributes={"fresh": False},
                    updated_at=self.now,
                )
            },
            config,
            now=self.now,
        ).outdoor_temperature

        self.assertEqual(degraded.quality.value, "degraded")
        self.assertEqual(stale.quality.value, "stale")

    def test_coordinator_publishes_running_snapshot_projection_without_writes(self) -> None:
        async def exercise() -> None:
            hass = FakeHass(self.states)
            entry = FakeEntry()
            runtime = ShadowRuntime(self.config)
            coordinator = ShadowCoordinator(hass, entry, self.config, runtime)
            entry.runtime_data = types.SimpleNamespace(snapshot=None, ux_snapshot=None)

            snapshot = await coordinator.async_start()
            published: list[object] = []
            remove_listener = coordinator.async_add_snapshot_listener(
                lambda: published.append(coordinator.snapshot)
            )
            self.assertEqual(len(registry.state_callbacks), 1)
            self.assertEqual(len(registry.time_callbacks), 1)
            self.assertEqual(registry.intervals[0], timedelta(seconds=60))
            self.states["sensor.bio_state"].state = "sleeping"
            registry.state_callbacks[0](None)
            await hass.tasks[-1]
            self.assertEqual(snapshot.inputs["bio_state"]["value"], "awake")
            self.assertEqual(entry.runtime_data.snapshot.inputs["bio_state"]["value"], "sleeping")
            self.assertEqual(len(published), 1)

            registry.time_callbacks[0](None)
            await hass.tasks[-1]
            self.assertIs(entry.runtime_data.snapshot, coordinator.snapshot)
            self.assertEqual(entry.runtime_data.ux_snapshot["version"], "blind_control.ux.v2")
            self.assertEqual(len(published), 2)
            self.assertFalse(coordinator.snapshot.actuation_executed)
            self.assertFalse(coordinator.snapshot.write_path_reachable)
            remove_listener()
            coordinator.stop()
            self.assertEqual(registry.unsubscribed, 2)

        with fake_home_assistant_event_modules() as registry:
            asyncio.run(exercise())

    def test_worker_callback_schedules_task_only_after_reaching_ha_event_loop(self) -> None:
        async def exercise() -> None:
            loop = asyncio.get_running_loop()
            hass = ThreadAwareFakeHass(self.states, loop)
            entry = FakeEntry()
            coordinator = ShadowCoordinator(hass, entry, self.config, ShadowRuntime(self.config))
            entry.runtime_data = types.SimpleNamespace(snapshot=None, ux_snapshot=None)
            await coordinator.async_start()

            await asyncio.to_thread(coordinator._state_changed, None)
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            await hass.tasks[-1]

            self.assertNotEqual(hass.add_job_thread_ids[-1], hass.loop_thread_id)
            self.assertEqual(hass.create_task_thread_ids[-1], hass.loop_thread_id)
            coordinator.stop()

        with fake_home_assistant_event_modules():
            asyncio.run(exercise())

    def test_coordinator_timer_uses_shortest_field_freshness(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {"outdoor_lux": "sensor.outdoor_lux"},
                "binding_freshness": {
                    "outdoor_lux": {
                        "max_age_seconds": 10,
                        "require_timestamp": True,
                        "owner": "solar_owner",
                    }
                },
            }
        )

        async def exercise() -> None:
            coordinator = ShadowCoordinator(
                FakeHass({}), FakeEntry(), config, ShadowRuntime(config)
            )
            await coordinator.async_start()
            self.assertEqual(registry.intervals[0], timedelta(seconds=300))
            coordinator.stop()

        with fake_home_assistant_event_modules() as registry:
            asyncio.run(exercise())

    def test_coordinator_derives_lux_trend_from_distinct_fresh_observations(self) -> None:
        config = BlindControlConfig.from_mapping(
            {"input_bindings": {"outdoor_lux": "sensor.owner_lux"}}
        )
        first_time = self.now - timedelta(seconds=10)
        states = {"sensor.owner_lux": FakeState("12000", updated_at=first_time)}

        async def exercise() -> None:
            hass = FakeHass(states)
            entry = FakeEntry()
            coordinator = ShadowCoordinator(hass, entry, config, ShadowRuntime(config))
            entry.runtime_data = types.SimpleNamespace(snapshot=None, ux_snapshot=None)

            first = await coordinator.async_refresh()
            self.assertEqual(
                first.inputs["lux_trend"]["reason"],
                "derived_lux_trend_waiting_for_previous_sample",
            )

            states["sensor.owner_lux"] = FakeState("9000", updated_at=self.now)
            second = await coordinator.async_refresh()
            self.assertEqual(second.inputs["lux_trend"]["value"], -3000.0)
            self.assertEqual(second.inputs["lux_trend"]["quality"], "fresh")
            self.assertEqual(
                second.inputs["lux_trend"]["reason"],
                "derived_from_consecutive_fresh_lux_observations",
            )
            self.assertIn("lux_trend", second.trace.solar.derived_evidence)

        asyncio.run(exercise())

    def test_legacy_field_with_stale_evidence_is_error_not_silent_parity(self) -> None:
        old = self.now - timedelta(seconds=1000)
        states = {**self.states, "sensor.legacy_apply": FakeState("shadow_ready", updated_at=old)}
        legacy = build_legacy_evidence_from_states(states, self.config, now=self.now)
        snapshot = ShadowRuntime(self.config).evaluate(
            build_inputs_from_states(self.states, self.config, now=self.now),
            legacy_snapshot=legacy,
        )

        apply_diff = next(diff for diff in snapshot.diffs if diff.field == "apply_status")
        self.assertEqual(apply_diff.classification, DiffClassification.ERROR)
        self.assertEqual(apply_diff.legacy_quality, "stale")


if __name__ == "__main__":
    unittest.main()
