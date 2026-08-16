from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import types
import unittest
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components" / "blind_control"


class _FakeSchema:
    def __init__(self, schema):
        self.schema = schema


class _FakeSection:
    def __init__(self, schema, options):
        self.schema = schema
        self.options = options


class _FakeSelector:
    def __init__(self, config):
        self.config = config


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


class _FakeSensorEntity:
    async def async_added_to_hass(self):
        return None

    def async_on_remove(self, callback):
        self._remove_callbacks = [*getattr(self, "_remove_callbacks", []), callback]

    def async_write_ha_state(self):
        self._state_write_count = getattr(self, "_state_write_count", 0) + 1

    async def async_will_remove_from_hass(self):
        for callback in getattr(self, "_remove_callbacks", []):
            callback()
        self._remove_callbacks = []


class _FakeEntityRegistry:
    def __init__(self):
        self.entries = {}

    def register(self, entity):
        unique_id = getattr(entity, "_attr_unique_id", None)
        self.entries[unique_id] = {
            "unique_id": unique_id,
            "translation_key": getattr(entity, "_attr_translation_key", None),
        }

    def remove(self, entity):
        self.entries.pop(getattr(entity, "_attr_unique_id", None), None)


class _FakeHomeAssistant:
    def __init__(self):
        self.data = {}
        self.http = _FakeHttp()
        self.entity_registry = _FakeEntityRegistry()
        self._entities_by_entry = {}
        self._entries = {}
        self._state_values = {}
        self.states = types.SimpleNamespace(get=lambda entity_id: self._state_values.get(entity_id))
        self.config_entries = types.SimpleNamespace(
            reloads=[],
            updates=[],
            forwards=[],
            unloads=[],
            async_reload=self._async_reload,
            async_update_entry=self._async_update_entry,
            async_forward_entry_setups=self._async_forward_entry_setups,
            async_unload_platforms=self._async_unload_platforms,
        )

    async def _async_reload(self, entry_id):
        """Mirror HA 2026.8 async_reload(entry_id) and rebuild runtime state."""

        self.config_entries.reloads.append(entry_id)
        entry = self._entries[entry_id]
        module = importlib.import_module("custom_components.blind_control")
        await module.async_unload_entry(self, entry)
        callbacks = list(entry.unload_callbacks)
        entry.unload_callbacks.clear()
        for callback in callbacks:
            callback()
        await module.async_setup_entry(self, entry)

    def _async_update_entry(self, entry, *, options):
        self.config_entries.updates.append((entry, options))

    async def _async_forward_entry_setups(self, entry, platforms):
        self._entries[entry.entry_id] = entry
        names = tuple(getattr(platform, "value", platform) for platform in platforms)
        self.config_entries.forwards.append((entry.entry_id, names))
        added = []

        def async_add_entities(entities):
            added.extend(entities)

        for name in names:
            module = importlib.import_module(f"custom_components.blind_control.{name}")
            await module.async_setup_entry(self, entry, async_add_entities)
        for entity in added:
            entity.hass = self
            self.entity_registry.register(entity)
            await entity.async_added_to_hass()
        self._entities_by_entry[entry.entry_id] = added

    async def _async_unload_platforms(self, entry, platforms):
        names = tuple(getattr(platform, "value", platform) for platform in platforms)
        self.config_entries.unloads.append((entry.entry_id, names))
        for entity in self._entities_by_entry.pop(entry.entry_id, []):
            await entity.async_will_remove_from_hass()
            self.entity_registry.remove(entity)
        return True


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


class _FakeEventModule(types.ModuleType):
    def __init__(self):
        super().__init__("homeassistant.helpers.event")
        self.state_callbacks = []
        self.time_callbacks = []

    def async_track_state_change_event(self, _hass, _entity_ids, callback):
        self.state_callbacks.append(callback)
        return lambda: self.state_callbacks.remove(callback)

    def async_track_time_interval(self, _hass, callback, _interval):
        self.time_callbacks.append(callback)
        return lambda: self.time_callbacks.remove(callback)


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


def _schema_value(schema: _FakeSchema, key: str):
    for schema_key, value in schema.schema.items():
        if getattr(schema_key, "key", schema_key) == key:
            return value
    raise KeyError(key)


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
    core.callback = lambda function: function
    data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
    data_entry_flow.section = lambda schema, options: _FakeSection(schema, options)
    helpers = types.ModuleType("homeassistant.helpers")
    event = _FakeEventModule()
    selector_module = types.ModuleType("homeassistant.helpers.selector")
    selector_module.selector = lambda config: _FakeSelector(config)
    helpers.selector = selector_module
    helpers.event = event
    components = types.ModuleType("homeassistant.components")
    websocket_api = _FakeWebsocket()
    frontend = _FakeFrontend("homeassistant.components.frontend")
    http = types.ModuleType("homeassistant.components.http")
    http.StaticPathConfig = _FakeStaticPathConfig
    sensor = types.ModuleType("homeassistant.components.sensor")
    sensor.SensorEntity = _FakeSensorEntity
    const = types.ModuleType("homeassistant.const")
    const.Platform = types.SimpleNamespace(SENSOR="sensor")
    const.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
    entity_platform.AddConfigEntryEntitiesCallback = object
    components.websocket_api = websocket_api
    components.frontend = frontend
    components.http = http
    components.sensor = sensor
    homeassistant.config_entries = config_entries
    homeassistant.core = core
    homeassistant.data_entry_flow = data_entry_flow
    homeassistant.helpers = helpers
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
            "homeassistant.const": const,
            "homeassistant.data_entry_flow": data_entry_flow,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.selector": selector_module,
            "homeassistant.helpers.event": event,
            "homeassistant.helpers.entity_platform": entity_platform,
            "homeassistant.components": components,
            "homeassistant.components.websocket_api": websocket_api,
            "homeassistant.components.frontend": frontend,
            "homeassistant.components.http": http,
            "homeassistant.components.sensor": sensor,
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
            self.assertEqual(hass.config_entries.forwards, [("entry-1", ("sensor",))])
            self.assertTrue(asyncio.run(module.async_unload_entry(hass, entry)))
            self.assertEqual(hass.config_entries.unloads, [("entry-1", ("sensor",))])

    def test_native_status_projection_is_registry_backed_redacted_and_unloads(self) -> None:
        with _home_assistant_imports():
            module = importlib.import_module("custom_components.blind_control")
            contracts = importlib.import_module("custom_components.blind_control.contracts")
            hass = _FakeHomeAssistant()
            entry = _FakeConfigEntry("entry-1")

            asyncio.run(module.async_setup_entry(hass, entry))
            sensor = hass._entities_by_entry[entry.entry_id][0]
            registry_entry = hass.entity_registry.entries[sensor._attr_unique_id]
            self.assertEqual(registry_entry["unique_id"], "entry-1_shadow_status")
            self.assertEqual(registry_entry["translation_key"], "status")
            self.assertEqual(sensor.native_value, "failure")
            initial_attributes = sensor.extra_state_attributes
            self.assertEqual(initial_attributes["failure_status"], "apply_blocked")
            self.assertTrue(initial_attributes["failure_quality_blockers"])
            self.assertIn(
                "bio_state",
                {blocker["key"] for blocker in initial_attributes["failure_quality_blockers"]},
            )

            def fresh(value, source):
                return contracts.InputObservation(
                    value=value,
                    source=source,
                    quality=contracts.InputQuality.FRESH,
                )

            inputs = contracts.BlindControlInputs(
                bio_state=fresh("awake", "sensor.fixture_bio"),
                activity_state=fresh("none", "sensor.fixture_activity"),
                day_state=fresh("forenoon", "sensor.fixture_day"),
                day_context=fresh("weekday", "sensor.fixture_context"),
                away=fresh(False, "sensor.fixture_away"),
                private_time=fresh(False, "sensor.fixture_private_time"),
                privacy=fresh(False, "sensor.fixture_privacy"),
                opening_state=fresh("closed", "sensor.fixture_opening"),
                opening_safe_for_blind=fresh(True, "sensor.fixture_opening"),
                cover_available=fresh(True, "sensor.fixture_cover"),
                cover_ready=fresh(True, "sensor.fixture_cover"),
                cover_position=fresh(42.0, "sensor.fixture_cover"),
                outdoor_lux=fresh(14_000.0, "sensor.fixture_lux"),
                lux_trend=fresh(0.0, "sensor.fixture_lux"),
                sun_elevation=fresh(30.0, "sensor.fixture_sun"),
                sun_azimuth=fresh(304.0, "sensor.fixture_sun"),
                expected_direct_radiation=fresh(400.0, "sensor.fixture_weather"),
                expected_diffuse_radiation=fresh(50.0, "sensor.fixture_weather"),
                cloud_cover=fresh(0.1, "sensor.fixture_weather"),
                indoor_temperature=fresh(22.0, "sensor.fixture_indoor"),
                outdoor_temperature=fresh(20.0, "sensor.fixture_outdoor"),
            )
            entry.runtime_data.snapshot = entry.runtime_data.shadow.evaluate(inputs)
            entry.runtime_data.coordinator._notify_snapshot_listeners()

            self.assertEqual(sensor.native_value, "normal")
            self.assertGreater(sensor._state_write_count, 0)
            attributes = sensor.extra_state_attributes
            self.assertEqual(attributes["active_category"], "neutral")
            self.assertEqual(attributes["failure_status"], "none")
            self.assertEqual(attributes["failure_quality_blockers"], [])
            self.assertFalse(attributes["safety_blocked"])
            self.assertFalse(attributes["apply_blocked"])
            serialized = json.dumps(attributes)
            self.assertNotIn("sensor.fixture", serialized)

            unresolved_inputs = replace(
                inputs,
                indoor_temperature=contracts.InputObservation(
                    value=22.0,
                    source="sensor.fixture_indoor",
                    quality=contracts.InputQuality.STALE,
                    reason="matrix_stale",
                ),
            )
            entry.runtime_data.snapshot = entry.runtime_data.shadow.evaluate(unresolved_inputs)
            entry.runtime_data.coordinator._notify_snapshot_listeners()
            self.assertEqual(sensor.native_value, "failure")
            failure_attributes = sensor.extra_state_attributes
            self.assertEqual(
                failure_attributes["failure_reason"],
                "automatic_decision_quality_gate_blocked",
            )
            self.assertIn(
                "indoor_temperature",
                {blocker["key"] for blocker in failure_attributes["failure_quality_blockers"]},
            )
            self.assertNotIn("sensor.fixture", json.dumps(failure_attributes))

            writes_before_unload = sensor._state_write_count
            self.assertTrue(asyncio.run(module.async_unload_entry(hass, entry)))
            entry.runtime_data.coordinator._notify_snapshot_listeners()
            self.assertEqual(sensor._state_write_count, writes_before_unload)
            self.assertEqual(hass.entity_registry.entries, {})

    def test_reload_re_registers_panel_and_options_listener_reloads_entry(self) -> None:
        with _home_assistant_imports():
            module = importlib.import_module("custom_components.blind_control")
            hass = _FakeHomeAssistant()
            now = datetime.now(UTC)
            old_binding = "sensor.owner_old"
            new_binding = "sensor.owner_new"
            entry = _FakeConfigEntry(
                "entry-1",
                data={"input_bindings": {"bio_state": old_binding}},
            )
            hass._state_values = {
                old_binding: types.SimpleNamespace(
                    state="sleep",
                    attributes={},
                    last_updated=now,
                    last_changed=now,
                ),
                new_binding: types.SimpleNamespace(
                    state="awake",
                    attributes={},
                    last_updated=now,
                    last_changed=now,
                ),
            }

            asyncio.run(module.async_setup(hass, {}))
            asyncio.run(module.async_setup(hass, {}))
            self.assertEqual(len(hass.http.static_paths), 1)
            self.assertEqual(len(hass.data["frontend_panels"]), 1)

            asyncio.run(module.async_setup_entry(hass, entry))
            self.assertEqual(len(entry.update_listeners), 1)
            old_runtime = entry.runtime_data
            old_coordinator = old_runtime.coordinator
            update_listener = entry.update_listeners[0]
            config_flow = importlib.import_module("custom_components.blind_control.config_flow")
            entry.options = config_flow._mapping_from_form(
                {"core_state_bindings": {"bio_state": new_binding}},
                old_runtime.config,
            )

            asyncio.run(update_listener(hass, entry))

            event = sys.modules["homeassistant.helpers.event"]
            self.assertEqual(hass.config_entries.reloads, ["entry-1"])
            self.assertIsNot(entry.runtime_data, old_runtime)
            self.assertIsNot(entry.runtime_data.coordinator, old_coordinator)
            self.assertEqual(old_coordinator._unsubscribers, [])
            self.assertEqual(old_coordinator._snapshot_listeners, [])
            self.assertEqual(len(entry.update_listeners), 1)
            self.assertEqual(len(event.state_callbacks), 1)
            self.assertEqual(len(event.time_callbacks), 1)
            self.assertEqual(
                entry.runtime_data.config.input_bindings, (("bio_state", new_binding),)
            )
            self.assertEqual(entry.runtime_data.snapshot.inputs["bio_state"]["value"], "awake")
            sensor = hass._entities_by_entry[entry.entry_id][0]
            self.assertEqual(sensor._snapshot.inputs["bio_state"]["value"], "awake")

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
                    "input_bindings": {"bio_state": "sensor.fixture_bio"},
                    "legacy_bindings": {"active_mode": "sensor.fixture_legacy"},
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
                        },
                    },
                )
            )
            self.assertEqual(len(hass.config_entries.updates), 1)
            self.assertFalse(hass.config_entries.updates[0][1]["apply_enabled"])
            binding_write = _FakeConnection(is_admin=True)
            asyncio.run(
                update_handler(
                    hass,
                    binding_write,
                    {
                        "id": 4,
                        "entry_id": "entry-1",
                        "options": {"input_bindings": {"activity_state": "sensor.new_activity"}},
                    },
                )
            )
            self.assertEqual(binding_write.errors[0][1], "invalid_options")
            self.assertEqual(len(hass.config_entries.updates), 1)

            read_only = _FakeConnection(is_admin=True)
            asyncio.run(get_handler(hass, read_only, {"id": 5, "entry_id": "entry-1"}))
            self.assertEqual(read_only.results[0][0], 5)
            projection = read_only.results[0][1]
            self.assertEqual(projection["version"], "blind_control.ux.v2")
            serialized = json.dumps(projection)
            self.assertNotIn("sensor.fixture_bio", serialized)
            self.assertNotIn("sensor.fixture_legacy", serialized)
            self.assertNotIn("sensor.new_activity", serialized)
            self.assertTrue(
                next(
                    field
                    for group in projection["settings"]["binding_groups"]
                    for field in group["fields"]
                    if field["key"] == "bio_state"
                )["configured"]
            )

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
            core_state_section = _schema_value(form["data_schema"], "core_state_bindings")
            self.assertIsInstance(core_state_section, _FakeSection)
            self.assertTrue(core_state_section.options["collapsed"])
            bio_selector = _schema_value(core_state_section.schema, "bio_state")
            self.assertIsInstance(bio_selector, _FakeSelector)
            self.assertEqual(bio_selector.config, {"entity": {}})
            opening_section = _schema_value(form["data_schema"], "opening_safety_cover_bindings")
            polarity_selector = _schema_value(opening_section.schema, "opening_safety_polarity")
            self.assertEqual(
                polarity_selector.config["select"]["translation_key"],
                "opening_safety_polarity",
            )

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
            user_input["core_state_bindings"] = {"bio_state": "sensor.bound_bio"}
            user_input["opening_safety_cover_bindings"] = {
                "opening_safety_polarity": "positive_safe"
            }
            user_input["solar_bindings"] = {}
            user_input["temperature_weather_bindings"] = {}
            user_input["legacy_comparison_bindings"] = {}

            result = asyncio.run(flow.async_step_user(user_input))
            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(result["title"], "Blind Control")
            self.assertEqual(result["data"]["config_version"], 2)
            self.assertEqual(result["data"]["input_bindings"], {"bio_state": "sensor.bound_bio"})
            self.assertEqual(result["data"]["opening_safety_polarity"], "positive_safe")
            existing = BlindControlConfig.from_mapping(result["data"])
            cleared = loaded._mapping_from_form(
                {"core_state_bindings": {"bio_state": ""}}, existing
            )
            self.assertNotIn("bio_state", cleared["input_bindings"])
            options_flow = loaded.BlindControlOptionsFlow(
                _FakeConfigEntry("entry-1", data=result["data"])
            )
            options_form = asyncio.run(options_flow.async_step_init())
            self.assertIsInstance(
                _schema_value(options_form["data_schema"], "solar_bindings"), _FakeSection
            )
            with self.assertRaises(_DuplicateEntry):
                asyncio.run(flow.async_step_user(user_input))


if __name__ == "__main__":
    unittest.main()
