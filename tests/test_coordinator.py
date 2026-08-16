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
    def __init__(self, state: str, *, attributes=None, updated_at=None):
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
            "sensor.day_state": FakeState("morning", updated_at=self.now),
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

    def test_stateful_owner_observation_is_not_staled_by_age_alone(self) -> None:
        old = self.now - timedelta(
            seconds=BlindControlConfig.defaults().observation_freshness_seconds + 1
        )
        states = {**self.states, "sensor.opening_state": FakeState("closed", updated_at=old)}
        inputs = build_inputs_from_states(states, self.config, now=self.now)

        self.assertTrue(inputs.opening_state.usable)
        self.assertEqual(inputs.opening_state.reason, "stateful_contract_not_age_limited")

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
        self.assertEqual(
            stale_inputs.cover_position.reason, "bound_entity_state_exceeded_freshness_window"
        )
        self.assertFalse(missing_inputs.cover_position.usable)
        self.assertEqual(missing_inputs.cover_position.reason, "required_timestamp_missing")

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
        self.assertEqual(
            inputs.cover_position.reason, "bound_entity_state_exceeded_freshness_window"
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
                "binding_freshness": {
                    "bio_state": {
                        "max_age_seconds": 1,
                        "require_timestamp": True,
                        "owner": "test_bio_owner",
                    }
                }
            }
        )

        self.assertEqual(config.binding_policy("bio_state").owner, "test_bio_owner")
        self.assertEqual(config.binding_policy("bio_state").max_age_seconds, 1)
        self.assertEqual(config.binding_policy("activity_state").owner, "core_state")
        self.assertIsNone(config.binding_policy("activity_state").max_age_seconds)
        self.assertEqual(config.binding_policy("cover_position").owner, "technical_device")

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
                "binding_freshness": {
                    "outdoor_lux": {
                        "max_age_seconds": 10,
                        "require_timestamp": True,
                        "owner": "solar_owner",
                    }
                }
            }
        )

        async def exercise() -> None:
            coordinator = ShadowCoordinator(
                FakeHass({}), FakeEntry(), config, ShadowRuntime(config)
            )
            await coordinator.async_start()
            self.assertEqual(registry.intervals[0], timedelta(seconds=5))
            coordinator.stop()

        with fake_home_assistant_event_modules() as registry:
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
