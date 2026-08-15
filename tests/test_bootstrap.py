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


class _SchemaKey:
    def __init__(self, key, required):
        self.key = key
        self.required = required

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return other == self.key or (
            isinstance(other, _SchemaKey)
            and self.key == other.key
            and self.required == other.required
        )

    def __repr__(self):
        return f"{self.required}({self.key!r})"


class _FakeVoluptuous(types.ModuleType):
    Schema = _FakeSchema

    @staticmethod
    def Required(key, **_kwargs):
        return _SchemaKey(key, "required")

    @staticmethod
    def Optional(key, **_kwargs):
        return _SchemaKey(key, "optional")

    @staticmethod
    def Coerce(value):
        return value

    @staticmethod
    def All(*values):
        return values

    @staticmethod
    def Range(**values):
        return values

    @staticmethod
    def In(values):
        return values


class _FakeConfigEntry:
    def __init__(self, entry_id: str, *, data=None, options=None):
        self.entry_id = entry_id
        self.domain = "blind_control"
        self.data = data or {}
        self.options = options or {}
        self.runtime_data = None
        self.unload_callbacks = []
        self.update_listeners = []

    def async_on_unload(self, callback):
        self.unload_callbacks.append(callback)
        return callback

    def add_update_listener(self, callback):
        self.update_listeners.append(callback)
        return lambda: self.update_listeners.remove(callback)

    @classmethod
    def __class_getitem__(cls, _item):
        return cls


class _FakeHomeAssistant:
    def __init__(self):
        self.data = {}
        self.http = _FakeHttp()
        self.config_entries = types.SimpleNamespace(
            reloads=[],
            updates=[],
            async_reload=self._async_reload,
            async_update_entry=self._async_update_entry,
        )

    async def _async_reload(self, domain, entry_id):
        self.config_entries.reloads.append((domain, entry_id))

    def _async_update_entry(self, entry, *, options):
        self.config_entries.updates.append((entry, options))


class _FakeStaticPathConfig:
    def __init__(self, url_path, path, cache_headers):
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers


class _FakeHttp:
    def __init__(self):
        self.static_paths = []

    async def async_register_static_paths(self, paths):
        if any(
            existing.url_path == path.url_path for existing in self.static_paths for path in paths
        ):
            raise RuntimeError("static path already registered")
        self.static_paths.extend(paths)


class _FakeFrontend(types.ModuleType):
    def async_register_built_in_panel(self, hass, **kwargs):
        hass.data.setdefault("frontend_panels", {})[kwargs["frontend_url_path"]] = kwargs

    def async_remove_panel(self, hass, url_path):
        hass.data.setdefault("frontend_panels", {}).pop(url_path, None)


class _FakeWebsocket(types.ModuleType):
    def __init__(self):
        super().__init__("homeassistant.components.websocket_api")
        self.commands = []

    def websocket_command(self, schema):
        def decorate(handler):
            handler.websocket_schema = schema
            return handler

        return decorate

    @staticmethod
    def async_response(handler):
        return handler

    @staticmethod
    def require_admin(handler):
        async def guarded(hass, connection, msg):
            if not getattr(getattr(connection, "user", None), "is_admin", False):
                connection.send_error(msg["id"], "unauthorized", "Admin required")
                return
            await handler(hass, connection, msg)

        guarded.requires_admin = True
        return guarded

    def async_register_command(self, _hass, handler):
        self.commands.append(handler)


class _FakeConnection:
    def __init__(self, *, is_admin):
        self.user = types.SimpleNamespace(is_admin=is_admin)
        self.results = []
        self.errors = []

    def send_result(self, message_id, result):
        self.results.append((message_id, result))

    def send_error(self, message_id, code, message):
        self.errors.append((message_id, code, message))


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

    def async_show_form(self, *, step_id, data_schema, **kwargs):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, **kwargs}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}


class _FakeOptionsFlow(_FakeConfigFlow):
    pass


@contextmanager
def _home_assistant_imports():
    voluptuous = _FakeVoluptuous("voluptuous")
    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = _FakeConfigEntry
    config_entries.ConfigFlow = _FakeConfigFlow
    config_entries.OptionsFlow = _FakeOptionsFlow
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = _FakeHomeAssistant
    components = types.ModuleType("homeassistant.components")
    websocket_api = _FakeWebsocket()
    frontend = _FakeFrontend("homeassistant.components.frontend")
    http = types.ModuleType("homeassistant.components.http")
    http.StaticPathConfig = _FakeStaticPathConfig
    components.websocket_api = websocket_api
    components.frontend = frontend
    components.http = http
    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.components = components
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
            "homeassistant.components": components,
            "homeassistant.components.websocket_api": websocket_api,
            "homeassistant.components.frontend": frontend,
            "homeassistant.components.http": http,
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

            self.assertTrue(asyncio.run(module.async_setup(hass, {})))
            self.assertIn("blind-control", hass.data["frontend_panels"])
            self.assertEqual(hass.http.static_paths[0].url_path, "/blind-control/frontend")
            self.assertTrue(asyncio.run(module.async_setup_entry(hass, entry)))
            self.assertIsInstance(entry.runtime_data, module.BlindControlRuntimeData)
            self.assertEqual(entry.runtime_data.phase, "shadow")
            self.assertIsNotNone(entry.runtime_data.snapshot)
            self.assertTrue(asyncio.run(module.async_unload_entry(hass, entry)))

    def test_reload_re_registers_panel_and_options_listener_reloads_entry(self) -> None:
        with _home_assistant_imports():
            module = importlib.import_module("custom_components.blind_control")
            hass = _FakeHomeAssistant()
            entry = _FakeConfigEntry("entry-1")

            asyncio.run(module.async_setup(hass, {}))
            asyncio.run(module.async_setup(hass, {}))
            self.assertEqual(len(hass.http.static_paths), 1)
            self.assertEqual(len(hass.data["frontend_panels"]), 1)

            asyncio.run(module.async_setup_entry(hass, entry))
            self.assertEqual(len(entry.update_listeners), 1)
            asyncio.run(entry.update_listeners[0](hass, entry))
            self.assertEqual(hass.config_entries.reloads, [("blind_control", "entry-1")])

    def test_websocket_contracts_read_and_admin_protect_options_write(self) -> None:
        with _home_assistant_imports():
            module = importlib.import_module("custom_components.blind_control")
            websocket = sys.modules["homeassistant.components.websocket_api"]
            websocket_api_module = importlib.import_module(
                "custom_components.blind_control.websocket_api"
            )
            hass = _FakeHomeAssistant()
            entry = _FakeConfigEntry(
                "entry-1",
                data={
                    "input_bindings": {"bio_state": "sensor.private_bio"},
                    "legacy_bindings": {"active_mode": "sensor.private_legacy"},
                },
            )
            asyncio.run(module.async_setup(hass, {}))
            asyncio.run(module.async_setup_entry(hass, entry))
            hass.config_entries.async_entries = lambda _domain: [entry]

            get_handler = next(
                handler
                for handler in websocket.commands
                if handler.websocket_schema["type"] == websocket_api_module.GET_SNAPSHOT
            )
            update_handler = next(
                handler
                for handler in websocket.commands
                if handler.websocket_schema["type"] == websocket_api_module.UPDATE_OPTIONS
            )
            update_schema = update_handler.websocket_schema
            required = {
                key.key
                for key in update_schema
                if isinstance(key, _SchemaKey) and key.required == "required"
            }
            optional = {
                key.key
                for key in update_schema
                if isinstance(key, _SchemaKey) and key.required == "optional"
            }
            self.assertIn("options", required)
            self.assertIn("entry_id", optional)
            self.assertTrue(get_handler.requires_admin)
            self.assertTrue(update_handler.requires_admin)

            denied = _FakeConnection(is_admin=False)
            asyncio.run(update_handler(hass, denied, {"id": 1, "options": {}}))
            self.assertEqual(denied.errors[0][1], "unauthorized")
            self.assertEqual(hass.config_entries.updates, [])

            denied_read = _FakeConnection(is_admin=False)
            asyncio.run(get_handler(hass, denied_read, {"id": 2, "entry_id": "entry-1"}))
            self.assertEqual(denied_read.errors[0][1], "unauthorized")
            self.assertEqual(denied_read.results, [])

            allowed = _FakeConnection(is_admin=True)
            asyncio.run(
                update_handler(
                    hass,
                    allowed,
                    {
                        "id": 3,
                        "entry_id": "entry-1",
                        "options": {
                            "apply_enabled": False,
                            "input_bindings": {"activity_state": "sensor.new_activity"},
                        },
                    },
                )
            )
            self.assertEqual(len(hass.config_entries.updates), 1)
            self.assertFalse(hass.config_entries.updates[0][1]["apply_enabled"])
            self.assertEqual(
                hass.config_entries.updates[0][1]["input_bindings"],
                {
                    "bio_state": "sensor.private_bio",
                    "activity_state": "sensor.new_activity",
                },
            )

            read_only = _FakeConnection(is_admin=True)
            asyncio.run(get_handler(hass, read_only, {"id": 4, "entry_id": "entry-1"}))
            self.assertEqual(read_only.results[0][0], 4)
            projection = read_only.results[0][1]
            self.assertEqual(projection["version"], "blind_control.ux.v1")
            serialized = json.dumps(projection)
            self.assertNotIn("sensor.private_bio", serialized)
            self.assertNotIn("sensor.private_legacy", serialized)
            self.assertNotIn("sensor.new_activity", serialized)
            self.assertTrue(projection["settings"]["binding_status"]["input_bindings"]["bio_state"])

    def test_config_flow_is_singleton_and_persists_shadow_configuration(self) -> None:
        if importlib.util.find_spec("homeassistant") is None:
            with self.assertRaises(ModuleNotFoundError):
                importlib.import_module("custom_components.blind_control.config_flow")

        with _home_assistant_imports():
            loaded = importlib.import_module("custom_components.blind_control.config_flow")
            flow = loaded.BlindControlConfigFlow()

            form = asyncio.run(flow.async_step_user())
            self.assertEqual(form["type"], "form")
            self.assertEqual(form["step_id"], "user")
            self.assertIn("window_azimuth", form["data_schema"].schema)
            self.assertIn("position_waking_normal", form["data_schema"].schema)

            from custom_components.blind_control.config import BlindControlConfig

            config = BlindControlConfig.defaults()
            user_input = {
                "window_azimuth": config.window_azimuth,
                "window_tilt": config.window_tilt,
                "axis_inverted": config.axis_inverted,
                "automation_enabled": config.automation_enabled,
                "apply_enabled": config.apply_enabled,
                "heat_outdoor_threshold": config.heat_outdoor_threshold,
                "heat_indoor_threshold": config.heat_indoor_threshold,
                "heat_radiation_threshold": config.heat_radiation_threshold,
                "heat_confidence_threshold": config.heat_confidence_threshold,
                "cloud_shadow_lux_drop": config.cloud_shadow_lux_drop,
                "cloud_shadow_ratio": config.cloud_shadow_ratio,
                "diffuse_lux_threshold": config.diffuse_lux_threshold,
                "night_lux_threshold": config.night_lux_threshold,
                "cold_outdoor_threshold": config.cold_outdoor_threshold,
                "cool_air_delta": config.cool_air_delta,
                "storm_precipitation_trend_threshold": config.storm_precipitation_trend_threshold,
                "storm_wind_trend_threshold": config.storm_wind_trend_threshold,
                "storm_pressure_drop_threshold": config.storm_pressure_drop_threshold,
                "storm_required_signals": config.storm_required_signals,
                "apply_cooldown_seconds": config.apply_cooldown_seconds,
                "position_tolerance": config.position_tolerance,
            }
            for name, profile in config.profiles:
                user_input[f"position_{name}_normal"] = profile.normal
                user_input[f"position_{name}_inverted"] = profile.inverted

            result = asyncio.run(flow.async_step_user(user_input))
            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(result["title"], "Blind Control")
            self.assertEqual(result["data"]["config_version"], 1)
            with self.assertRaises(_DuplicateEntry):
                asyncio.run(flow.async_step_user(user_input))


if __name__ == "__main__":
    unittest.main()
