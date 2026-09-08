"""Administrative staging, never an actuation service."""

import hashlib
import json

from .config import BlindControlConfig


def legacy_writer_blocker(hass):
    """Fail closed if a Legacy entry can run or its service is still registered."""
    entries = getattr(getattr(hass, "config_entries", None), "async_entries", None)
    if not callable(entries):
        return "legacy_writer_state_unavailable"
    for entry in entries("benni_blind_policy"):
        state = getattr(entry, "state", None)
        if not getattr(entry, "disabled_by", None) or getattr(state, "value", state) == "loaded":
            return "legacy_writer_not_disabled"
    has_service = getattr(getattr(hass, "services", None), "has_service", None)
    if not callable(has_service):
        return "legacy_service_state_unavailable"
    if has_service("benni_blind_policy", "apply_now"):
        return "legacy_service_still_registered_restart_required"
    return None


def revision(config):
    return hashlib.sha256(json.dumps(config.to_mapping(), sort_keys=True).encode()).hexdigest()


def runtime_matches(current, loaded):
    if loaded is None:
        return False
    persisted, runtime = current.to_mapping(), loaded.to_mapping()
    if not persisted["open_meteo_api_url"]:
        runtime["open_meteo_api_url"] = ""  # Non-persisted HA location prefill.
    return persisted == runtime


def staged_config(current, requested, *, expected_revision, confirmed, blocker):
    """Only arm from already staged Live/BC/OFF, never in a mode transition."""
    if expected_revision != revision(current):
        raise ValueError("operation_changed_refresh_required")
    if set(requested) != {"runtime_mode", "apply_owner", "apply_enabled"}:
        raise ValueError("invalid_operation_fields")
    candidate = BlindControlConfig.from_mapping({**current.to_mapping(), **requested})
    if candidate.apply_enabled:
        if (
            current.runtime_mode != "live"
            or current.apply_owner != "blind_control"
            or current.apply_enabled
            or candidate.runtime_mode != "live"
            or candidate.apply_owner != "blind_control"
        ):
            raise ValueError("stage_live_blind_control_apply_off_first")
        if confirmed is not True:
            raise ValueError("null_writer_confirmation_required")
        if blocker:
            raise ValueError(blocker)
    return candidate
