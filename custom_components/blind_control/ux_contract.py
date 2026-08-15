"""Versioned read-only UX projection for overview and diagnostics surfaces."""

from __future__ import annotations

from .config import BlindControlConfig
from .shadow import ShadowSnapshot

UX_CONTRACT_VERSION = "blind_control.ux.v1"


def build_ux_snapshot(snapshot: ShadowSnapshot, config: BlindControlConfig) -> dict[str, object]:
    """Build a typed-equivalent snapshot for a later Svelte 5 gateway.

    This projection has no command surface.  Settings are represented as data
    for rendering and validation; applying them remains the ConfigEntry/
    OptionsFlow boundary and never a cover-write path.
    """

    trace = snapshot.trace
    return {
        "version": UX_CONTRACT_VERSION,
        "overview": {
            "active_mode": trace.active_mode,
            "winner_keys": list(trace.winner_keys),
            "fachlicher_target": trace.fachlicher_target,
            "effective_target": trace.effective_target,
            "opening_state": trace.safety.opening_state,
            "safety_status": trace.safety.status,
            "apply_status": trace.apply.status,
            "override": trace.override.as_dict(),
            "shadow_only": snapshot.shadow_only,
        },
        "diagnosis": {
            "candidates": [candidate.as_dict() for candidate in trace.candidates],
            "paused_requirements": [item.as_dict() for item in trace.paused_requirements],
            "solar": trace.solar.as_dict(),
            "reasons": list(trace.reasons),
            "inputs": snapshot.inputs,
            "diffs": [diff.as_dict() for diff in snapshot.diffs],
        },
        "settings": {
            "axis_inverted": config.axis_inverted,
            "window_azimuth": config.window_azimuth,
            "window_tilt": config.window_tilt,
            "automation_enabled": config.automation_enabled,
            "apply_enabled": config.apply_enabled,
            "profiles": {name: profile.as_dict() for name, profile in config.profiles},
            "calibration_defaults": {
                "heat_outdoor_threshold": config.heat_outdoor_threshold,
                "heat_indoor_threshold": config.heat_indoor_threshold,
                "heat_radiation_threshold": config.heat_radiation_threshold,
                "heat_confidence_threshold": config.heat_confidence_threshold,
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
        "debug_payload": snapshot.debug_payload(),
    }
