"""Read-only Shadow snapshot and OptionsFlow-backed configuration transport."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from .config import BlindControlConfig
from .const import DOMAIN
from .ux_contract import build_ux_snapshot

GET_SNAPSHOT = "blind_control/get_snapshot"
UPDATE_OPTIONS = "blind_control/update_options"
_REGISTERED_ATTRIBUTE = "_blind_control_shadow_websocket_registered"

GET_SNAPSHOT_SCHEMA = {
    vol.Required("type"): GET_SNAPSHOT,
    vol.Optional("entry_id"): str,
}
UPDATE_OPTIONS_SCHEMA = {
    vol.Required("type"): UPDATE_OPTIONS,
    vol.Required("options"): dict,
    vol.Optional("entry_id"): str,
}


def register_websocket_commands(hass: object) -> None:
    """Register only read/projection commands once for this HA instance."""

    if getattr(hass, _REGISTERED_ATTRIBUTE, False):
        return
    try:
        from homeassistant.components import websocket_api
    except ImportError:
        return

    @websocket_api.websocket_command(GET_SNAPSHOT_SCHEMA)
    @websocket_api.require_admin
    @websocket_api.async_response
    async def _get_snapshot(hass, connection, msg) -> None:
        entry = _entry_for_message(hass, msg)
        if entry is None:
            connection.send_error(msg["id"], "not_loaded", "Blind Control entry is not loaded")
            return
        runtime_data = getattr(entry, "runtime_data", None)
        projection = getattr(runtime_data, "ux_snapshot", None)
        if projection is None:
            config = _entry_config(entry)
            snapshot = getattr(runtime_data, "snapshot", None)
            if snapshot is None:
                connection.send_error(
                    msg["id"], "snapshot_unavailable", "Shadow snapshot unavailable"
                )
                return
            projection = build_ux_snapshot(snapshot, config)
        connection.send_result(msg["id"], projection)

    @websocket_api.websocket_command(UPDATE_OPTIONS_SCHEMA)
    @websocket_api.require_admin
    @websocket_api.async_response
    async def _update_options(hass, connection, msg) -> None:
        entry = _entry_for_message(hass, msg)
        options = msg.get("options")
        if entry is None:
            connection.send_error(msg["id"], "not_loaded", "Blind Control entry is not loaded")
            return
        if not isinstance(options, Mapping):
            connection.send_error(msg["id"], "invalid_options", "Options must be a mapping")
            return
        try:
            current = _entry_config(entry)
            config = BlindControlConfig.from_mapping(_merge_options(current, options))
        except (TypeError, ValueError, KeyError) as error:
            connection.send_error(msg["id"], "invalid_options", str(error))
            return
        hass.config_entries.async_update_entry(entry, options=config.to_mapping())
        connection.send_result(msg["id"], {"ok": True})

    websocket_api.async_register_command(hass, _get_snapshot)
    websocket_api.async_register_command(hass, _update_options)
    setattr(hass, _REGISTERED_ATTRIBUTE, True)


def _merge_options(current: BlindControlConfig, options: Mapping[str, Any]) -> dict[str, object]:
    """Merge non-binding UX edits; entity selection stays in native OptionsFlow."""

    merged = current.to_mapping()
    for key, value in options.items():
        if key in {"input_bindings", "legacy_bindings", "binding_intents"}:
            raise ValueError("entity_bindings_require_native_options_flow")
        merged[key] = value
    return merged


def _entry_for_message(hass: object, msg: Mapping[str, Any]):
    entries = hass.config_entries.async_entries(DOMAIN)
    requested = msg.get("entry_id")
    for entry in entries:
        if requested is None or requested == getattr(entry, "entry_id", None):
            return entry
    return None


def _entry_config(entry: object) -> BlindControlConfig:
    return BlindControlConfig.from_mapping(
        {**getattr(entry, "data", {}), **getattr(entry, "options", {})}
    )
