from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components" / "blind_control"


class _FakeSchema:
    def __init__(self, schema):
        self.schema = schema


class _FakeVoluptuous(types.ModuleType):
    Schema = _FakeSchema


class _FakeConfigEntry:
    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        self.runtime_data = None

    @classmethod
    def __class_getitem__(cls, _item):
        return cls


class _FakeHomeAssistant:
    pass


class _DuplicateEntry(Exception):
    pass


class _FakeConfigFlow:
    configured_unique_ids: set[str] = set()

    def __init_subclass__(cls, **kwargs):
        kwargs.pop("domain", None)
        super().__init_subclass__(**kwargs)

    async def async_set_unique_id(self, unique_id: str):
        self._unique_id = unique_id

    def _abort_if_unique_id_configured(self):
        if self._unique_id in self.configured_unique_ids:
            raise _DuplicateEntry(self._unique_id)
        self.configured_unique_ids.add(self._unique_id)

    def async_show_form(self, *, step_id, data_schema):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}


@contextmanager
def _home_assistant_imports():
    voluptuous = _FakeVoluptuous("voluptuous")
    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = _FakeConfigEntry
    config_entries.ConfigFlow = _FakeConfigFlow
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = _FakeHomeAssistant
    homeassistant.config_entries = config_entries
    homeassistant.core = core
    _FakeConfigFlow.configured_unique_ids.clear()

    for name in tuple(sys.modules):
        if name == "custom_components.blind_control" or name.startswith(
            "custom_components.blind_control."
        ):
            sys.modules.pop(name, None)

    with patch.dict(
        sys.modules,
        {
            "voluptuous": voluptuous,
            "homeassistant": homeassistant,
            "homeassistant.config_entries": config_entries,
            "homeassistant.core": core,
        },
    ):
        try:
            yield
        finally:
            for name in tuple(sys.modules):
                if name == "custom_components.blind_control" or name.startswith(
                    "custom_components.blind_control."
                ):
                    sys.modules.pop(name, None)


class BootstrapTests(unittest.TestCase):
    def test_manifest_is_native_config_entry_bootstrap(self) -> None:
        manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["domain"], "blind_control")
        self.assertEqual(manifest["name"], "Blind Control")
        self.assertTrue(manifest["config_flow"])
        self.assertNotIn("platforms", manifest)

    def test_setup_and_unload_use_entry_runtime_data(self) -> None:
        with _home_assistant_imports():
            module = importlib.import_module("custom_components.blind_control")
            hass = _FakeHomeAssistant()
            entry = _FakeConfigEntry("entry-1")

            self.assertFalse(hasattr(hass, "data"))
            self.assertTrue(asyncio.run(module.async_setup(hass, {})))
            self.assertTrue(asyncio.run(module.async_setup_entry(hass, entry)))
            self.assertIsInstance(entry.runtime_data, module.BlindControlRuntimeData)
            self.assertEqual(entry.runtime_data.phase, "bootstrap")
            self.assertTrue(asyncio.run(module.async_unload_entry(hass, entry)))
            self.assertIsNone(entry.runtime_data)

    def test_config_flow_is_singleton_and_has_only_empty_user_step(self) -> None:
        if importlib.util.find_spec("homeassistant") is None:
            with self.assertRaises(ModuleNotFoundError):
                importlib.import_module("custom_components.blind_control.config_flow")

        with _home_assistant_imports():
            loaded = importlib.import_module("custom_components.blind_control.config_flow")
            flow = loaded.BlindControlConfigFlow()

            form = asyncio.run(flow.async_step_user())
            self.assertEqual(form["type"], "form")
            self.assertEqual(form["step_id"], "user")
            self.assertEqual(form["data_schema"].schema, {})

            result = asyncio.run(flow.async_step_user({}))
            self.assertEqual(result, {"type": "create_entry", "title": "Blind Control", "data": {}})
            with self.assertRaises(_DuplicateEntry):
                asyncio.run(flow.async_step_user({}))


if __name__ == "__main__":
    unittest.main()
