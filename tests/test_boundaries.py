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

    def test_product_code_has_no_actuation_or_active_apply_surface(self) -> None:
        forbidden = (
            "async_call",
            "async_register_service",
            "call_service",
            "set_cover_position",
        )
        for path in PACKAGE.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, source, f"{token} in {path}")

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
