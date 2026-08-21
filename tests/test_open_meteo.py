from __future__ import annotations

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
from custom_components.blind_control.contracts import (  # noqa: E402
    InputObservation,
    InputQuality,
)
from custom_components.blind_control.coordinator import (  # noqa: E402
    _radiation_provider_observations,
    build_inputs_from_states,
)
from custom_components.blind_control.open_meteo import (  # noqa: E402
    DIFFUSE_RADIATION_FIELD,
    DIRECT_RADIATION_FIELD,
    OPEN_METEO_FRESHNESS_SECONDS,
    OpenMeteoPayloadError,
    OpenMeteoRadiationData,
    OpenMeteoUrlError,
    normalize_open_meteo_url,
    parse_open_meteo_payload,
    suggested_open_meteo_url,
)


class FakeState:
    def __init__(self, state: str, updated_at: datetime):
        self.state = state
        self.attributes = {}
        self.last_updated = updated_at


class FakeProvider:
    def __init__(self, status: str, data: OpenMeteoRadiationData | None):
        self._status = status
        self.data = data

    def provider_status(self, *, now=None):
        return self._status


class OpenMeteoContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime.now(UTC)
        self.url = suggested_open_meteo_url(50.1, 8.6, "Europe/Berlin")

    def test_suggested_url_has_fixed_current_contract_without_key_or_pv(self) -> None:
        normalized = normalize_open_meteo_url(self.url + "&utm_source=test")

        self.assertIn("api.open-meteo.com/v1/forecast", normalized)
        self.assertIn("models=dwd_icon_seamless", normalized)
        self.assertIn(DIRECT_RADIATION_FIELD, normalized)
        self.assertIn(DIFFUSE_RADIATION_FIELD, normalized)
        self.assertNotIn("utm_source", normalized)
        self.assertNotIn("api_key", normalized)
        self.assertNotIn("pv", normalized.lower())

    def test_url_validation_rejects_unsafe_or_wrong_contracts(self) -> None:
        valid_query = self.url.split("?", 1)[1]
        cases = (
            f"http://api.open-meteo.com/v1/forecast?{valid_query}",
            f"https://example.invalid/v1/forecast?{valid_query}",
            f"https://user@api.open-meteo.com/v1/forecast?{valid_query}",
            self.url.replace("dwd_icon_seamless", "other_model"),
            self.url.replace(f"%2C{DIFFUSE_RADIATION_FIELD}", ""),
            self.url + "&api_key=secret",
            self.url + "&pv_power=10",
            self.url.replace("Europe%2FBerlin", "api_key%3Dsecret"),
        )
        for value in cases:
            with self.subTest(value=value), self.assertRaises(OpenMeteoUrlError):
                normalize_open_meteo_url(value)

    def test_one_payload_keeps_dni_diffuse_and_valid_zero_distinct(self) -> None:
        data = parse_open_meteo_payload(
            {
                "current": {
                    "time": "2026-08-21T12:00",
                    DIRECT_RADIATION_FIELD: 321,
                    DIFFUSE_RADIATION_FIELD: 87,
                }
            },
            fetched_at=self.now,
        )
        night = parse_open_meteo_payload(
            {
                "current": {
                    DIRECT_RADIATION_FIELD: 0,
                    DIFFUSE_RADIATION_FIELD: 0,
                }
            },
            fetched_at=self.now,
        )

        self.assertEqual(data.direct_normal_irradiance, 321)
        self.assertEqual(data.diffuse_radiation, 87)
        self.assertEqual(night.direct_normal_irradiance, 0)
        self.assertEqual(night.diffuse_radiation, 0)

    def test_incomplete_or_non_numeric_payload_is_not_defaulted(self) -> None:
        cases = (
            {},
            {"current": {DIRECT_RADIATION_FIELD: 10}},
            {
                "current": {
                    DIRECT_RADIATION_FIELD: "bad",
                    DIFFUSE_RADIATION_FIELD: 10,
                }
            },
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(OpenMeteoPayloadError):
                parse_open_meteo_payload(payload, fetched_at=self.now)

    def test_provider_observation_fresh_degraded_stale_and_first_failure(self) -> None:
        data = OpenMeteoRadiationData(240, 80, self.now, "redacted-time")
        for status, expected_quality in (
            ("ready", InputQuality.FRESH),
            ("degraded", InputQuality.FRESH),
            ("stale", InputQuality.STALE),
        ):
            observations = _radiation_provider_observations(
                FakeProvider(status, data),
                now=self.now + timedelta(seconds=OPEN_METEO_FRESHNESS_SECONDS + 1),
            )
            with self.subTest(status=status):
                self.assertEqual(
                    observations["expected_direct_radiation"].quality,
                    expected_quality,
                )

        unavailable = _radiation_provider_observations(
            FakeProvider("unavailable", None), now=self.now
        )
        self.assertEqual(
            unavailable["expected_direct_radiation"].quality,
            InputQuality.UNAVAILABLE,
        )
        self.assertIsNone(unavailable["expected_direct_radiation"].value)

    def test_external_binding_wins_before_internal_provider(self) -> None:
        config = BlindControlConfig.from_mapping(
            {
                "open_meteo_api_url": self.url,
                "input_bindings": {"expected_direct_radiation": "sensor.external_radiation"},
            }
        )
        provider = {
            "expected_direct_radiation": InputObservation(
                300.0,
                source="internal_open_meteo",
                quality=InputQuality.FRESH,
                updated_at=self.now,
            ),
            "expected_diffuse_radiation": InputObservation(
                90.0,
                source="internal_open_meteo",
                quality=InputQuality.FRESH,
                updated_at=self.now,
            ),
        }
        inputs = build_inputs_from_states(
            {"sensor.external_radiation": FakeState("500", self.now)},
            config,
            now=self.now,
            provider_observations=provider,
        )

        self.assertEqual(inputs.expected_direct_radiation.value, 500)
        self.assertEqual(inputs.expected_direct_radiation.source, "sensor.external_radiation")
        self.assertEqual(inputs.expected_diffuse_radiation.value, 90)
        self.assertEqual(inputs.expected_diffuse_radiation.source, "internal_open_meteo")


if __name__ == "__main__":
    unittest.main()
