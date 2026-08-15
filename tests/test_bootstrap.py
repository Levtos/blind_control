from __future__ import annotations

import asyncio
import importlib
import json
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components" / "blind_control"


class _FakeSchema:
    def __init__(self, schema):
        self.schema = schema


class _FakeVoluptuous(types.ModuleType):
    Schema = _FakeSchema


class _FakeConfigFlow:
    def __init_subclass__(cls, **kwargs):
        kwargs.pop("domain", None)
        super().__init_subclass__(**kwargs)

    def async_show_form(self, *, step_id, data_schema):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}


@contextmanager
def _home_assistant_imports():
    voluptuous = _FakeVoluptuous("voluptuous")
    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigFlow = _FakeConfigFlow
    homeassistant.config_entries = config_entries

    with patch.dict(
        sys.modules,
        {
            "voluptuous": voluptuous,
            "homeassistant": homeassistant,
            "homeassistant.config_entries": config_entries,
        },
    ):
        yield


class BootstrapTests(unittest.TestCase):
    def test_manifest_is_native_config_entry_bootstrap(self) -> None:
        manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["domain"], "blind_control")
        self.assertEqual(manifest["name"], "Blind Control")
        self.assertTrue(manifest["config_flow"])
        self.assertNotIn("platforms", manifest)

    def test_setup_and_unload_are_reproducible_without_write_surface(self) -> None:
        module = importlib.import_module("custom_components.blind_control")
        hass = SimpleNamespace(data={})
        entry = SimpleNamespace(entry_id="entry-1")

        self.assertTrue(asyncio.run(module.async_setup(hass, {})))
        self.assertTrue(asyncio.run(module.async_setup_entry(hass, entry)))
        self.assertIn("blind_control", hass.data)
        self.assertIn("entry-1", hass.data["blind_control"])
        self.assertTrue(asyncio.run(module.async_unload_entry(hass, entry)))
        self.assertEqual(hass.data["blind_control"], {})

    def test_config_flow_has_only_empty_user_step_and_empty_entry(self) -> None:
        module = importlib.import_module("custom_components.blind_control.config_flow")
        try:
            with _home_assistant_imports():
                loaded = importlib.reload(module)
                flow = loaded.BlindControlConfigFlow()

                form = asyncio.run(flow.async_step_user())
                self.assertEqual(form["type"], "form")
                self.assertEqual(form["step_id"], "user")
                self.assertEqual(form["data_schema"].schema, {})

                result = asyncio.run(flow.async_step_user({}))
                self.assertEqual(
                    result, {"type": "create_entry", "title": "Blind Control", "data": {}}
                )
        finally:
            importlib.reload(module)


if __name__ == "__main__":
    unittest.main()
