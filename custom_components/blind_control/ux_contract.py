"""Versioned read-only UX projection for overview and diagnostics surfaces."""

from __future__ import annotations

from .config import BINDING_GROUPS, BlindControlConfig, binding_requirement, binding_status
from .contracts import redact_diagnostic_value
from .core_inputs import FIELDS
from .open_meteo import (
    OPEN_METEO_MODEL,
    OPEN_METEO_PROVIDER,
    OPEN_METEO_UPDATE_INTERVAL_SECONDS,
)
from .shadow import ShadowSnapshot

UX_CONTRACT_VERSION = "blind_control.ux.v5"
AUTOMATION_PROJECTION_VERSION = "blind_control.automation_projection.v4"


def build_ux_snapshot(
    snapshot: ShadowSnapshot,
    config: BlindControlConfig,
    *,
    provider_status: str = "unconfigured",
) -> dict[str, object]:
    """Build a typed-equivalent snapshot for a later Svelte 5 gateway.

    This projection has no command surface.  Settings are represented as data
    for rendering and validation; applying them remains the ConfigEntry/
    OptionsFlow boundary and never a cover-write path.
    """

    trace = snapshot.trace
    trace_projection = redact_diagnostic_value(trace.as_dict())
    debug_payload = snapshot.debug_payload()
    input_values = debug_payload.get("inputs", {})

    if not isinstance(trace_projection, dict):
        trace_projection = {}
    if not isinstance(input_values, dict):
        input_values = {}

    def input_value(key: str):
        observation = input_values.get(key, {})
        return observation.get("value") if isinstance(observation, dict) else None

    winner = trace_projection.get("winner")
    failure = trace_projection.get("failure", {})
    active_branches = trace_projection.get("active_branches", [])
    technical = {
        "opening_state": trace.safety.opening_state,
        "safety": trace_projection.get("safety", {}),
        "apply": trace_projection.get("apply", {}),
        "cover_available": input_value("cover_available"),
        "cover_ready": input_value("cover_ready"),
        "shadow_only": snapshot.shadow_only,
        "actuation_executed": snapshot.actuation_executed,
        "write_path_reachable": snapshot.write_path_reachable,
        "runtime_mode": config.runtime_mode,
        "apply_owner": config.apply_owner,
    }
    automation_projection = build_automation_projection(snapshot)
    return {
        "version": UX_CONTRACT_VERSION,
        "evaluated_at": snapshot.evaluated_at.isoformat(),
        "overview": {
            "decision": trace_projection.get("decision"),
            "environment_values": {
                key: input_value(key)
                if input_values.get(key, {}).get("quality") == "fresh"
                else None
                for key in (
                    "outdoor_lux",
                    "outdoor_temperature",
                    "indoor_temperature",
                    "cover_motion",
                )
            },
            "master_mode": trace.master_mode.value,
            "winner": winner,
            "active_branches": active_branches,
            "failure": failure,
            "active_mode": trace.active_mode,
            "winner_keys": list(trace.winner_keys),
            "fachlicher_target": trace.fachlicher_target,
            "effective_target": trace.effective_target,
            "opening_state": trace.safety.opening_state,
            "cover_position": input_value("cover_position")
            if input_values.get("cover_position", {}).get("quality") == "fresh"
            else None,
            "physical_target": snapshot.physical_target,
            "movement_status": snapshot.movement_status,
            "baseline_position": snapshot.baseline_position,
            "baseline_ready": snapshot.baseline_ready,
            "movement_error": snapshot.movement_error,
            "recovery_status": snapshot.recovery_status,
            "household": {
                key: input_value(key)
                for key in (
                    "bio_state",
                    "activity_state",
                    "day_state",
                    "day_context",
                    "away",
                    "private_time",
                    "privacy",
                )
            },
            "safety_status": trace.safety.status,
            "apply_status": trace.apply.status,
            "override": trace_projection.get("override", {}),
            "technical": technical,
            "shadow_only": snapshot.shadow_only,
            "actuation_executed": snapshot.actuation_executed,
            "write_path_reachable": snapshot.write_path_reachable,
        },
        "diagnosis": {
            "decision": trace_projection.get("decision"),
            "apply_off_effect": "Prevents new commands; does not stop an already accepted physical move.",
            "environment": snapshot.environment,
            "hierarchy": {
                "master_mode": trace.master_mode.value,
                "winner": winner,
                "active_branches": active_branches,
                "failure": failure,
                "legacy_flat": {
                    "active_mode": trace.active_mode,
                    "winner_keys": list(trace.winner_keys),
                },
            },
            "candidates": trace_projection.get("candidates", []),
            "paused_requirements": trace_projection.get("paused_requirements", []),
            "solar": trace_projection.get("solar", {}),
            "reasons": trace_projection.get("reasons", list(trace.reasons)),
            "inputs": input_values,
            "diffs": debug_payload.get("diffs", []),
            "legacy_evidence": debug_payload.get("legacy_evidence", {}),
            "radiation_provider": {
                "provider": OPEN_METEO_PROVIDER,
                "model": OPEN_METEO_MODEL,
                "status": provider_status,
                "update_interval": OPEN_METEO_UPDATE_INTERVAL_SECONDS,
            },
        },
        "settings": {
            "core_contracts": dict(config.core_contracts),
            "core_contract_profile": config.core_contract_profile,
            "axis_inverted": config.axis_inverted,
            "window_azimuth": config.window_azimuth,
            "window_tilt": config.window_tilt,
            "automation_enabled": config.automation_enabled,
            "apply_enabled": config.apply_enabled,
            "runtime_mode": config.runtime_mode,
            "apply_owner": config.apply_owner,
            "opening_safety_polarity": config.opening_safety_polarity,
            "binding_groups": _binding_groups(config, provider_status=provider_status),
            "observation_freshness_seconds": config.observation_freshness_seconds,
            "binding_freshness": config.binding_freshness_mapping(),
            "profiles": {name: profile.as_dict() for name, profile in config.profiles},
            "calibration_defaults": {
                "heat_outdoor_threshold": config.heat_outdoor_threshold,
                "heat_indoor_threshold": config.heat_indoor_threshold,
                "heat_radiation_threshold": config.heat_radiation_threshold,
                "heat_confidence_threshold": config.heat_confidence_threshold,
                "glare_confidence_threshold": config.glare_confidence_threshold,
                "cloud_shadow_lux_drop": config.cloud_shadow_lux_drop,
                "cloud_cover_threshold": config.cloud_cover_threshold,
                "model_lux_ratio": config.model_lux_ratio,
                "minimum_incidence_factor": config.minimum_incidence_factor,
                "model_lux_per_watt": config.model_lux_per_watt,
                "cold_lux_enter_threshold": config.cold_lux_enter_threshold,
                "cold_lux_exit_threshold": config.cold_lux_exit_threshold,
                "environment_hysteresis_ratio": config.environment_hysteresis_ratio,
                "environment_enter_seconds": config.environment_enter_seconds,
                "environment_exit_seconds": config.environment_exit_seconds,
                "movement_recovery_seconds": config.movement_recovery_seconds,
                "position_settle_seconds": config.position_settle_seconds,
                "movement_timeout_seconds": config.movement_timeout_seconds,
                "cool_air_delta": config.cool_air_delta,
                "storm_required_signals": config.storm_required_signals,
                "diffuse_lux_threshold": config.diffuse_lux_threshold,
                "night_lux_threshold": config.night_lux_threshold,
                "cold_outdoor_threshold": config.cold_outdoor_threshold,
                "storm_precipitation_trend_threshold": config.storm_precipitation_trend_threshold,
                "storm_wind_trend_threshold": config.storm_wind_trend_threshold,
                "storm_pressure_drop_threshold": config.storm_pressure_drop_threshold,
                "apply_cooldown_seconds": config.apply_cooldown_seconds,
                "position_tolerance": config.position_tolerance,
            },
        },
        "automation_projection": automation_projection,
        "debug_payload": debug_payload,
    }


def build_automation_projection(snapshot: ShadowSnapshot) -> dict[str, object]:
    """Return the single, redacted read-only contract shared by HA and UX.

    The fields are deliberately small enough for an entity state projection and
    expose no bindings, raw source values, services, or actuator controls.
    ``winner_*`` remains as a compatible name while ``active_*`` is the native
    automation-facing vocabulary.
    """

    trace = snapshot.trace
    winner = trace.winner
    projection = {
        "version": AUTOMATION_PROJECTION_VERSION,
        "decision": redact_diagnostic_value(trace.decision.as_dict()) if trace.decision else None,
        "master_mode": trace.master_mode.value,
        "active_category": winner.category if winner else None,
        "active_variant": winner.variant if winner else None,
        "winner_category": winner.category if winner else None,
        "winner_variant": winner.variant if winner else None,
        "fachlicher_target": trace.fachlicher_target,
        "effective_target": trace.effective_target,
        "physical_target": snapshot.physical_target,
        "movement_status": snapshot.movement_status,
        "movement_error": snapshot.movement_error,
        "recovery_status": snapshot.recovery_status,
        "failure_status": trace.failure.status,
        "failure_reason": trace.failure.reason,
        "failure_quality_blockers": [
            blocker.as_dict() for blocker in trace.failure.quality_blockers
        ],
        "safety_status": trace.safety.status,
        "apply_status": trace.apply.status,
        "safety_blocked": trace.safety.status == "blocked",
        "apply_blocked": trace.apply.status == "blocked",
        "shadow_only": snapshot.shadow_only,
        "actuation_executed": snapshot.actuation_executed,
        "write_path_reachable": snapshot.write_path_reachable,
        "runtime_mode": trace.apply.runtime_mode,
        "apply_owner": trace.apply.apply_owner,
    }
    redacted = redact_diagnostic_value(projection)
    return redacted if isinstance(redacted, dict) else {}


def _binding_groups(
    config: BlindControlConfig,
    *,
    provider_status: str = "unconfigured",
) -> list[dict[str, object]]:
    """Project optional binding slots without returning their private entity IDs."""

    input_bindings = dict(config.input_bindings)
    legacy_bindings = dict(config.legacy_bindings)
    groups: list[dict[str, object]] = []
    for key, label, fields, legacy in BINDING_GROUPS:
        bindings = legacy_bindings if legacy else input_bindings
        projected_fields = []
        for field in fields:
            status = binding_status(config, field, legacy=legacy)
            if not legacy and any(field in FIELDS[schema] for schema, _ in config.core_contracts):
                status = "core_contract_selected"
            if (
                not legacy
                and field in {"expected_direct_radiation", "expected_diffuse_radiation"}
                and field not in bindings
            ):
                status = {
                    "ready": "internal_provider_active",
                    "degraded": "internal_provider_degraded",
                    "stale": "provider_stale",
                }.get(provider_status, "provider_unavailable")
            projected_fields.append(
                {
                    "key": field,
                    "configured": field in bindings,
                    "requirement": binding_requirement(field, legacy=legacy),
                    "status": status,
                    **config.binding_policy(field, legacy=legacy).as_dict(),
                }
            )
        missing_required = [
            field["key"]
            for field in projected_fields
            if field["status"] in {"required_unresolved", "conditional_unresolved"}
        ]
        groups.append(
            {
                "key": key,
                "label": label,
                "readiness": "ready" if not missing_required else "missing_required",
                "missing_required": missing_required,
                "fields": projected_fields,
            }
        )
    return groups
