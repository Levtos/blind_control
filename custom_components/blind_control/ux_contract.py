"""Versioned read-only UX projection for overview and diagnostics surfaces."""

from __future__ import annotations

from .config import INPUT_BINDING_KEYS, LEGACY_BINDING_KEYS, BlindControlConfig
from .contracts import redact_diagnostic_value
from .shadow import ShadowSnapshot

UX_CONTRACT_VERSION = "blind_control.ux.v1"


def build_ux_snapshot(snapshot: ShadowSnapshot, config: BlindControlConfig) -> dict[str, object]:
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

    return {
        "version": UX_CONTRACT_VERSION,
        "evaluated_at": snapshot.evaluated_at.isoformat(),
        "overview": {
            "active_mode": trace.active_mode,
            "winner_keys": list(trace.winner_keys),
            "fachlicher_target": trace.fachlicher_target,
            "effective_target": trace.effective_target,
            "opening_state": trace.safety.opening_state,
            "cover_position": input_value("cover_position"),
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
            "shadow_only": snapshot.shadow_only,
            "actuation_executed": snapshot.actuation_executed,
            "write_path_reachable": snapshot.write_path_reachable,
        },
        "diagnosis": {
            "candidates": trace_projection.get("candidates", []),
            "paused_requirements": trace_projection.get("paused_requirements", []),
            "solar": trace_projection.get("solar", {}),
            "reasons": trace_projection.get("reasons", list(trace.reasons)),
            "inputs": input_values,
            "diffs": debug_payload.get("diffs", []),
            "legacy_evidence": debug_payload.get("legacy_evidence", {}),
        },
        "settings": {
            "axis_inverted": config.axis_inverted,
            "window_azimuth": config.window_azimuth,
            "window_tilt": config.window_tilt,
            "automation_enabled": config.automation_enabled,
            "apply_enabled": config.apply_enabled,
            "input_bindings": {key: "" for key in INPUT_BINDING_KEYS},
            "legacy_bindings": {key: "" for key in LEGACY_BINDING_KEYS},
            "binding_status": {
                "input_bindings": {
                    key: key in dict(config.input_bindings) for key in INPUT_BINDING_KEYS
                },
                "legacy_bindings": {
                    key: key in dict(config.legacy_bindings) for key in LEGACY_BINDING_KEYS
                },
            },
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
                "cloud_shadow_ratio": config.cloud_shadow_ratio,
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
        "debug_payload": debug_payload,
    }
