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

from custom_components.blind_control.migration import (  # noqa: E402
    ConsumerReference,
    RenameMigrationPlan,
)


class RenameMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = RenameMigrationPlan(
            old_entity_id="cover.legacy_blind",
            new_entity_id="cover.living_thermal_blind",
            consumers=(
                ConsumerReference("config_entry", "blind_control.cover_position"),
                ConsumerReference("automation", "automation.cutover_fixture"),
                ConsumerReference("dashboard", "dashboard.cutover_fixture"),
            ),
        )

    def test_exact_recursive_migration_and_rollback_are_lossless(self) -> None:
        source = {
            "entity": "cover.legacy_blind",
            "list": ["cover.legacy_blind", "cover.legacy_blind_battery"],
            "nested": {"cover.legacy_blind": {"target": "cover.legacy_blind"}},
        }

        migrated = self.plan.migrate(source)
        rolled_back = self.plan.rollback(migrated)

        self.assertEqual(migrated["entity"], "cover.living_thermal_blind")
        self.assertEqual(migrated["list"][1], "cover.legacy_blind_battery")
        self.assertEqual(rolled_back, source)

    def test_public_inventory_summary_is_redacted_and_counted(self) -> None:
        summary = self.plan.public_summary()

        self.assertEqual(summary["consumer_count"], 3)
        self.assertEqual(summary["consumers_by_surface"]["config_entry"], 1)
        self.assertNotIn("legacy_blind", str(summary))
        self.assertTrue(summary["rollback_prepared"])

    def test_invalid_or_identity_rename_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RenameMigrationPlan("sensor.not_cover", "cover.new", ())
        with self.assertRaises(ValueError):
            RenameMigrationPlan("cover.same", "cover.same", ())


if __name__ == "__main__":
    unittest.main()
