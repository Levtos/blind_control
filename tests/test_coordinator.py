from __future__ import annotations

import asyncio
import sys
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

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


class FakeEntry:
    def __init__(self):
        self.runtime_data = None


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
                "closed", attributes={"current_position": 42}, updated_at=self.now
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

    def test_stale_owner_observation_is_visible_and_not_used_as_fresh_input(self) -> None:
        old = self.now - timedelta(
            seconds=BlindControlConfig.defaults().observation_freshness_seconds + 1
        )
        states = {**self.states, "sensor.opening_state": FakeState("closed", updated_at=old)}
        inputs = build_inputs_from_states(states, self.config, now=self.now)

        self.assertFalse(inputs.opening_state.usable)
        self.assertEqual(inputs.opening_state.quality.value, "stale")

    def test_coordinator_publishes_running_snapshot_projection_without_writes(self) -> None:
        hass = FakeHass(self.states)
        entry = FakeEntry()
        runtime = ShadowRuntime(self.config)
        coordinator = ShadowCoordinator(hass, entry, self.config, runtime)
        entry.runtime_data = types.SimpleNamespace(snapshot=None, ux_snapshot=None)

        snapshot = asyncio.run(coordinator.async_start())

        self.assertIs(entry.runtime_data.snapshot, snapshot)
        self.assertEqual(entry.runtime_data.ux_snapshot["version"], "blind_control.ux.v1")
        self.assertEqual(snapshot.inputs["bio_state"]["value"], "awake")
        self.assertFalse(snapshot.actuation_executed)
        self.assertFalse(snapshot.write_path_reachable)
        coordinator.stop()

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
