from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "blind_control"
if "custom_components.blind_control" not in sys.modules:
    package = types.ModuleType("custom_components.blind_control")
    package.__path__ = [str(PACKAGE)]
    sys.modules["custom_components.blind_control"] = package

from custom_components.blind_control.binding_suggestions import (  # noqa: E402
    discover_binding_suggestions,
)
from custom_components.blind_control.config import (  # noqa: E402
    CONDITIONAL_BINDING_KEYS,
    INPUT_BINDING_KEYS,
    LEGACY_BINDING_KEYS,
    MANDATORY_AUTOMATIC_BINDING_KEYS,
    MANDATORY_TECHNICAL_BINDING_KEYS,
    OPTIONAL_EVIDENCE_BINDING_KEYS,
    BlindControlConfig,
    binding_status,
)
from custom_components.blind_control.open_meteo import suggested_open_meteo_url  # noqa: E402


class FakeState:
    def __init__(self, entity_id: str, state: object, attributes=None) -> None:
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, states) -> None:
        self._states = states

    def async_all(self):
        return self._states


class FakeHass:
    def __init__(self, states) -> None:
        self.states = FakeStates(states)


def contract_states() -> list[FakeState]:
    source_entities = {
        "source_bio_state": "sensor.contract_bio",
        "source_activity_state": "sensor.contract_activity",
        "source_day_state": "sensor.contract_day",
        "source_day_context": "sensor.contract_day_context",
        "source_presence": "sensor.contract_presence",
        "source_opening_contract_state": "sensor.contract_opening",
        "source_cover_state": "cover.contract_blind",
        "source_cover_current_position": "cover.contract_blind",
        "source_lux": "sensor.contract_lux",
        "source_sun_state": "sun.contract_sun",
        "source_weather": "sensor.contract_weather",
    }
    return [
        FakeState(
            "sensor.contract_blind_master",
            "ready",
            {
                "kind": "master",
                "slug": "living_blind",
                "current_cover_position": 42,
                "cover_available": True,
                "opening_state": "closed",
                "source_entities": source_entities,
            },
        ),
        FakeState(
            "sensor.contract_bio",
            "awake",
            {"options": ["sleep", "provisional_sleep", "waking", "awake"]},
        ),
        FakeState(
            "sensor.contract_activity",
            "music",
            {"pc_active": True, "entertainment_active": False, "private": False},
        ),
        FakeState("sensor.contract_day", "forenoon"),
        FakeState("sensor.contract_day_context", "werktag"),
        FakeState("sensor.contract_presence", "zuhause", {"away_gate": False}),
        FakeState("sensor.contract_privacy", "off", {"slug": "privacy_candidate"}),
        FakeState("sensor.contract_opening", "closed", {"kind": "master"}),
        FakeState(
            "binary_sensor.contract_opening_unsafe",
            "off",
            {"slug": "opening_unsafe_for_rollo"},
        ),
        FakeState("cover.contract_blind", "closed", {"current_position": 42}),
        FakeState(
            "binary_sensor.contract_blind_ready",
            "on",
            {"cover_available": True, "current_position": 42, "policy_context_ready": True},
        ),
        FakeState("sensor.contract_lux", "12000", {"variant": "lux"}),
        FakeState("sun.contract_sun", "above_horizon", {"elevation": 31, "azimuth": 145}),
        FakeState(
            "sensor.contract_climate",
            "ready",
            {"kind": "master", "slug": "climate_living", "temperature": 23.1},
        ),
        FakeState(
            "sensor.contract_weather",
            "ready",
            {"outdoor_temperature": 14.2, "cloud_coverage": 56},
        ),
        FakeState(
            "sensor.contract_dni",
            "310",
            {"blind_control_evidence": "direct_normal_irradiance_instant"},
        ),
        FakeState(
            "sensor.contract_diffuse",
            "95",
            {"blind_control_evidence": "diffuse_radiation_instant"},
        ),
        FakeState(
            "sensor.contract_legacy_debug",
            "shadow",
            {
                "active_mode": "heat",
                "active_position": 15,
                "apply_enabled": True,
                "blockers": [],
            },
        ),
    ]


class BindingSuggestionTests(unittest.TestCase):
    def test_contract_discovery_resolves_all_required_bindings_and_safe_polarity(self) -> None:
        suggestions = discover_binding_suggestions(
            FakeHass(contract_states()), BlindControlConfig.defaults()
        )

        required = MANDATORY_AUTOMATIC_BINDING_KEYS | MANDATORY_TECHNICAL_BINDING_KEYS
        self.assertEqual(set(suggestions.input_bindings) & required, required)
        self.assertEqual(suggestions.opening_safety_polarity, "negative_unsafe")
        self.assertEqual(set(suggestions.legacy_bindings), set(LEGACY_BINDING_KEYS))
        self.assertNotIn("lux_trend", suggestions.input_bindings)
        self.assertNotIn("expected_direct_radiation", suggestions.input_bindings)
        self.assertNotIn("expected_diffuse_radiation", suggestions.input_bindings)

    def test_contract_prefill_is_deterministic_and_ignores_generic_master_distractors(self) -> None:
        states = [
            state for state in contract_states() if state.entity_id != "sensor.contract_weather"
        ]
        states[0].attributes["source_entities"].pop("source_weather", None)
        states.extend(
            [
                FakeState(
                    "sensor.generic_blind_master",
                    "ready",
                    {
                        "kind": "master",
                        "slug": "living_blind_secondary",
                        "current_cover_position": 20,
                        "cover_available": True,
                        "opening_state": "closed",
                        "privacy_candidate": True,
                    },
                ),
                FakeState(
                    "binary_sensor.privacy_owner",
                    "off",
                    {"role": "privacy", "quality_status": "fresh"},
                ),
                FakeState(
                    "sensor.indoor_temperature_canonical",
                    "23.5",
                    {
                        "slug": "indoor_temperature",
                        "device_class": "temperature",
                        "temperature": 23.5,
                    },
                ),
                FakeState(
                    "climate.unrelated",
                    "heat",
                    {"kind": "master", "slug": "climate_unrelated", "temperature": 19.0},
                ),
                FakeState(
                    "weather.home",
                    "sunny",
                    {"temperature": 14.2, "device_class": "temperature"},
                ),
            ]
        )

        forward = discover_binding_suggestions(FakeHass(states), BlindControlConfig.defaults())
        reverse = discover_binding_suggestions(
            FakeHass(list(reversed(states))), BlindControlConfig.defaults()
        )

        self.assertEqual(forward.input_bindings, reverse.input_bindings)
        self.assertNotIn("privacy", forward.input_bindings)
        self.assertEqual(
            forward.input_bindings["indoor_temperature"],
            "sensor.indoor_temperature_canonical",
        )
        self.assertEqual(forward.input_bindings["outdoor_temperature"], "weather.home")

    def test_generic_climate_master_is_not_an_indoor_temperature_contract(self) -> None:
        suggestions = discover_binding_suggestions(
            FakeHass(
                [
                    FakeState(
                        "climate.generic",
                        "heat",
                        {
                            "kind": "master",
                            "slug": "climate_unrelated",
                            "temperature": 19.0,
                        },
                    )
                ]
            ),
            BlindControlConfig.defaults(),
        )

        self.assertNotIn("indoor_temperature", suggestions.input_bindings)

    def test_retired_privacy_candidates_are_not_suggested(self) -> None:
        states = [
            FakeState(
                "sensor.generic_blind_master",
                "ready",
                {
                    "kind": "master",
                    "slug": "living_blind",
                    "current_cover_position": 42,
                    "cover_available": True,
                    "opening_state": "closed",
                    "privacy_candidate": True,
                },
            ),
            FakeState(
                "binary_sensor.living_privacy_signal",
                "off",
                {
                    "slug": "living_rollo_privacy_candidate",
                    "output_type": "boolean",
                    "derived": {"privacy": False},
                    "degraded": False,
                },
            ),
        ]

        forward = discover_binding_suggestions(FakeHass(states), BlindControlConfig.defaults())
        reverse = discover_binding_suggestions(
            FakeHass(list(reversed(states))), BlindControlConfig.defaults()
        )

        self.assertNotIn("privacy", forward.input_bindings)
        self.assertEqual(forward.input_bindings, reverse.input_bindings)

    def test_existing_empty_intent_removes_a_stale_binding_from_prefill(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {"activity_state": "sensor.old_activity"},
                "binding_intents": {"activity_state": "intentionally_empty"},
            }
        )

        suggestions = discover_binding_suggestions(FakeHass(contract_states()), config)

        self.assertNotIn("activity_state", suggestions.input_bindings)

    def test_existing_choices_and_intentionally_empty_slots_override_prefill(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "input_bindings": {"activity_state": "sensor.user_selected"},
                "binding_intents": {
                    "activity_state": "bound",
                    "cloud_cover": "intentionally_empty",
                },
                "opening_safety_polarity": "positive_safe",
            }
        )

        suggestions = discover_binding_suggestions(FakeHass(contract_states()), config)

        self.assertEqual(suggestions.input_bindings["activity_state"], "sensor.user_selected")
        self.assertNotIn("cloud_cover", suggestions.input_bindings)
        self.assertEqual(suggestions.opening_safety_polarity, "positive_safe")

    def test_exact_binding_classification_and_status_vocabulary(self) -> None:
        self.assertEqual(len(INPUT_BINDING_KEYS), 28)
        self.assertEqual(len(MANDATORY_AUTOMATIC_BINDING_KEYS), 11)
        self.assertEqual(len(MANDATORY_TECHNICAL_BINDING_KEYS), 4)
        self.assertEqual(len(CONDITIONAL_BINDING_KEYS), 1)
        self.assertEqual(len(OPTIONAL_EVIDENCE_BINDING_KEYS), 12)
        self.assertEqual(len(LEGACY_BINDING_KEYS), 4)

        empty = BlindControlConfig.defaults()
        for key in MANDATORY_AUTOMATIC_BINDING_KEYS | MANDATORY_TECHNICAL_BINDING_KEYS:
            self.assertEqual(binding_status(empty, key), "required_unresolved")
        radiation_fields = {"expected_direct_radiation", "expected_diffuse_radiation"}
        self.assertEqual(binding_status(empty, "privacy"), "derived_from_day_state")
        for key in OPTIONAL_EVIDENCE_BINDING_KEYS - radiation_fields - {"privacy"}:
            self.assertEqual(binding_status(empty, key), "optional_intentionally_empty")
        for key in radiation_fields:
            self.assertEqual(binding_status(empty, key), "provider_unavailable")

        internal = BlindControlConfig.from_mapping(
            {"open_meteo_api_url": suggested_open_meteo_url(50, 8, "Europe/Berlin")}
        )
        for key in radiation_fields:
            self.assertEqual(binding_status(internal, key), "internal_provider_active")

        external = BlindControlConfig.from_mapping(
            {
                **internal.to_mapping(),
                "input_bindings": {"expected_direct_radiation": "sensor.external_contract"},
            }
        )
        self.assertEqual(
            binding_status(external, "expected_direct_radiation"),
            "external_override_active",
        )
        self.assertEqual(
            binding_status(empty, next(iter(CONDITIONAL_BINDING_KEYS))),
            "conditional_not_applicable",
        )
        for key in LEGACY_BINDING_KEYS:
            self.assertEqual(binding_status(empty, key, legacy=True), "legacy_not_available")


if __name__ == "__main__":
    unittest.main()
