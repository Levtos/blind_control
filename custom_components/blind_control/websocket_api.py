"""Read-only snapshot and non-critical configuration transport."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from .config import BlindControlConfig
from .const import DOMAIN
from .operation import legacy_writer_blocker, revision, runtime_matches, staged_config
from .ux_contract import build_ux_snapshot

GET_SNAPSHOT = "blind_control/get_snapshot"
UPDATE_OPTIONS = "blind_control/update_options"
SET_OPERATION = "blind_control/set_operation"
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
SET_OPERATION_SCHEMA = {
    vol.Required("type"): SET_OPERATION,
    vol.Required("operation"): dict,
    vol.Required("expected_revision"): str,
    vol.Optional("confirm_null_writer", default=False): bool,
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
        current = _entry_config(entry)
        loaded = getattr(runtime_data, "config", None)
        shadow = getattr(runtime_data, "shadow", None)
        active = getattr(shadow, "active", False)
        pending = not active or not runtime_matches(current, loaded)
        blocker = legacy_writer_blocker(hass)
        operation = {
            "revision": revision(current),
            "pending": pending,
            "legacy_blocker": blocker,
            "runtime_generation": getattr(shadow, "runtime_generation", None),
            "decision_generation": getattr(shadow, "decision_generation", None),
            "lease_status": "revoked"
            if pending
            else "latest"
            if getattr(shadow, "latest_snapshot", None) is not None
            else "consumed_or_invalidated",
            "armed": not pending
            and not blocker
            and current.automation_enabled
            and current.apply_enabled
            and current.runtime_mode == "live"
            and current.apply_owner == "blind_control",
        }
        connection.send_result(msg["id"], {**projection, "operation": operation})

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
        from .operation import revoke_entry_runtime

        if config.to_mapping() != current.to_mapping():
            revoke_entry_runtime(entry)
            hass.config_entries.async_update_entry(entry, options=config.to_mapping())
        connection.send_result(msg["id"], {"ok": True})

    @websocket_api.websocket_command(SET_OPERATION_SCHEMA)
    @websocket_api.require_admin
    @websocket_api.async_response
    async def _set_operation(hass, connection, msg) -> None:
        entry = _entry_for_message(hass, msg)
        runtime = getattr(entry, "runtime_data", None)
        shadow = getattr(runtime, "shadow", None)
        if shadow is None or not shadow.active:
            connection.send_error(msg["id"], "not_loaded", "Betriebswechsel wird noch geladen")
            return
        try:
            current = _entry_config(entry)
            if not runtime_matches(current, getattr(runtime, "config", None)):
                raise ValueError("runtime_reload_pending")
            config = staged_config(
                current,
                msg["operation"],
                expected_revision=msg["expected_revision"],
                confirmed=msg.get("confirm_null_writer"),
                blocker=legacy_writer_blocker(hass),
            )
            # Revoke old approvals synchronously before persisting/reloading.
            if config.to_mapping() != current.to_mapping():
                shadow.stop()
                hass.config_entries.async_update_entry(entry, options=config.to_mapping())
        except (TypeError, ValueError, KeyError) as error:
            connection.send_error(msg["id"], "invalid_operation", str(error))
            return
        connection.send_result(msg["id"], {"ok": True})

    websocket_api.async_register_command(hass, _get_snapshot)
    websocket_api.async_register_command(hass, _update_options)
    websocket_api.async_register_command(hass, _set_operation)
    setattr(hass, _REGISTERED_ATTRIBUTE, True)


def _merge_options(current: BlindControlConfig, options: Mapping[str, Any]) -> dict[str, object]:
    """Merge non-binding UX edits; entity selection stays in native OptionsFlow."""

    merged = current.to_mapping()
    if current.apply_enabled and any(
        key in options and options[key] != merged[key]
        for key in ("core_contracts", "core_contract_profile")
    ):
        raise ValueError("disable_apply_before_contract_change")
    for key, value in options.items():
        if key in {
            "input_bindings",
            "legacy_bindings",
            "binding_intents",
            "open_meteo_api_url",
            "runtime_mode",
            "apply_owner",
            "apply_enabled",
        }:
            raise ValueError("safety_critical_options_require_native_options_flow")
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
