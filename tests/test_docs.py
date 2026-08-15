from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components" / "blind_control"
DOCS = ROOT / "docs"


class DocumentationTests(unittest.TestCase):
    def test_normative_documents_exist(self) -> None:
        for filename in (
            "LASTENHEFT.md",
            "ARCHITECTURE.md",
            "INVENTORY.md",
            "CONTRACTS.md",
            "MIGRATION.md",
        ):
            self.assertTrue((DOCS / filename).is_file(), filename)

        lastenheft = (DOCS / "LASTENHEFT.md").read_text(encoding="utf-8")
        for term in (
            "Dokumentversion:** 0.2",
            "direct_sun",
            "cloud_shadow",
            "diffuse_bright",
            "solar_not_on_window",
            "storm_approaching",
            "cool_air_available",
            "cold_insulation",
            "Override",
            "A1–A16",
            "A16 Restart",
            "124° OSO",
        ):
            self.assertIn(term, lastenheft)

    def test_contract_document_contains_versioned_examples_and_decisions(self) -> None:
        source = (DOCS / "CONTRACTS.md").read_text(encoding="utf-8")
        for term in (
            "mapping contract v1.5.0",
            "activity decision v1.0.0",
            "opening.v1",
            "weather_environment.v1",
            "technical_device.v1",
            "sensor.benni_core_state_bio_state",
            "cover.wohnbereich_thermo_verdunklungsrollo",
            "unknown",
            "reject",
        ):
            self.assertIn(term, source)

    def test_inventory_classifies_every_required_surface(self) -> None:
        source = (DOCS / "INVENTORY.md").read_text(encoding="utf-8")
        for term in (
            "ConfigEntry",
            "Storage",
            "WebSocket",
            "entity.py",
            "websocket_api.py",
            "apply_now",
            "set_privacy_bed",
            "clear_manual_override",
            "set_position_profile",
            "get_status",
            "set_apply_enabled",
            "set_manual_position",
            "set_manual_decision",
            "set_invert_position",
            "reset_position_profile",
            "set_heat_lux_min",
            "Apply",
            "Cooldown",
            "Writing guard",
            "Override",
            "Startup",
            "EVENT_HOMEASSISTANT_STARTED",
            "Regression",
            "Consumer",
            "ungeklärt / Blocker",
        ):
            self.assertIn(term, source)

    def test_translation_key_sets_match(self) -> None:
        def key_paths(value, prefix=()):
            if isinstance(value, dict):
                paths = set()
                for key, child in value.items():
                    paths.update(key_paths(child, prefix + (key,)))
                return paths
            return {prefix}

        source = json.loads((PACKAGE / "strings.json").read_text(encoding="utf-8"))
        source_keys = key_paths(source)
        for locale in ("de", "en"):
            translated = json.loads(
                (PACKAGE / "translations" / f"{locale}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(source_keys, key_paths(translated), locale)

    def test_relative_document_links_resolve(self) -> None:
        link_pattern = re.compile(r"\]\((?!https?://|#)([^)]+)\)")
        for path in (
            DOCS / "LASTENHEFT.md",
            DOCS / "ARCHITECTURE.md",
            DOCS / "INVENTORY.md",
            DOCS / "CONTRACTS.md",
            DOCS / "MIGRATION.md",
        ):
            source = path.read_text(encoding="utf-8")
            for target in link_pattern.findall(source):
                self.assertTrue((path.parent / target).exists(), f"{path}: {target}")


if __name__ == "__main__":
    unittest.main()
