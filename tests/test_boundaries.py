from __future__ import annotations

import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "blind_control"
ENTITY_ID = re.compile(
    r"\b(?:binary_sensor|climate|cover|input_boolean|lock|media_player|sensor|sun|switch|weather)\.[a-z0-9_]+\b"
)


class BoundaryTests(unittest.TestCase):
    def test_product_code_has_no_entity_ids_or_private_endpoints(self) -> None:
        for path in PACKAGE.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertIsNone(ENTITY_ID.search(source), path.as_posix())
            self.assertNotIn("192.168.", source, path.as_posix())
            self.assertNotIn("SUPERVISOR_TOKEN", source, path.as_posix())

    def test_only_guarded_apply_adapter_contains_actuation_surface(self) -> None:
        forbidden = (
            "async_call",
            "async_register_service",
            "call_service",
            "set_cover_position",
        )
        for path in PACKAGE.rglob("*.py"):
            if path.name == "apply.py":
                continue
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, source, f"{token} in {path}")
        adapter = (PACKAGE / "apply.py").read_text(encoding="utf-8")
        self.assertEqual(adapter.count("async_call("), 1)
        self.assertIn('self.config.runtime_mode == "live"', adapter)
        self.assertIn('self.config.apply_owner == "blind_control"', adapter)
        self.assertIn("self.config.apply_enabled", adapter)
        self.assertIn("decision.status not in _READY_STATUSES", adapter)

    def test_internal_provider_has_no_api_key_pv_or_actuation_contract(self) -> None:
        product_source = "\n".join(
            path.read_text(encoding="utf-8") for path in PACKAGE.rglob("*.py")
        ).lower()
        for forbidden in ("photovoltaic", "pv_array", "pv_power", "yield_forecast"):
            self.assertNotIn(forbidden, product_source)
        provider = (PACKAGE / "radiation_provider.py").read_text(encoding="utf-8")
        contract = (PACKAGE / "open_meteo.py").read_text(encoding="utf-8")
        config_flow = (PACKAGE / "config_flow.py").read_text(encoding="utf-8")
        self.assertEqual(provider.count("session.get("), 1)
        self.assertIn('OPEN_METEO_HOST = "api.open-meteo.com"', contract)
        self.assertIn('OPEN_METEO_MODEL = "dwd_icon_seamless"', contract)
        self.assertNotIn('"api_key"', config_flow)
        self.assertNotIn('"api_key"', contract)
        self.assertNotIn("str(self._api_url)", provider)

    def test_only_read_only_sensor_platform_is_forwarded(self) -> None:
        source = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
        sensor = (PACKAGE / "sensor.py").read_text(encoding="utf-8")

        self.assertIn("PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)", source)
        self.assertIn("async_forward_entry_setups(entry, PLATFORMS)", source)
        self.assertIn("async_unload_platforms(entry, PLATFORMS)", source)
        self.assertIn("SensorEntity", sensor)
        self.assertNotIn("async_call", sensor)


if __name__ == "__main__":
    unittest.main()
