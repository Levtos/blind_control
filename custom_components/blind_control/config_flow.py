"""ConfigEntry and OptionsFlow for the non-actuating AP2 shadow runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow

from .config import DEFAULT_PROFILE_NAMES, BlindControlConfig
from .const import DOMAIN


def _config_schema(config: BlindControlConfig | None = None):
    config = config or BlindControlConfig.defaults()
    fields: dict[object, object] = {
        vol.Required("window_azimuth", default=config.window_azimuth): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=360)
        ),
        vol.Required("window_tilt", default=config.window_tilt): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=180)
        ),
        vol.Required("axis_inverted", default=config.axis_inverted): vol.In([True, False]),
        vol.Required("automation_enabled", default=config.automation_enabled): vol.In(
            [True, False]
        ),
        vol.Required("apply_enabled", default=config.apply_enabled): vol.In([True, False]),
        vol.Required("heat_outdoor_threshold", default=config.heat_outdoor_threshold): vol.Coerce(
            float
        ),
        vol.Required("heat_indoor_threshold", default=config.heat_indoor_threshold): vol.Coerce(
            float
        ),
        vol.Required(
            "heat_radiation_threshold", default=config.heat_radiation_threshold
        ): vol.Coerce(float),
        vol.Required(
            "heat_confidence_threshold", default=config.heat_confidence_threshold
        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
        vol.Required("cloud_shadow_lux_drop", default=config.cloud_shadow_lux_drop): vol.Coerce(
            float
        ),
        vol.Required("cloud_shadow_ratio", default=config.cloud_shadow_ratio): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1)
        ),
        vol.Required("diffuse_lux_threshold", default=config.diffuse_lux_threshold): vol.Coerce(
            float
        ),
        vol.Required("night_lux_threshold", default=config.night_lux_threshold): vol.Coerce(float),
        vol.Required("cold_outdoor_threshold", default=config.cold_outdoor_threshold): vol.Coerce(
            float
        ),
        vol.Required("cool_air_delta", default=config.cool_air_delta): vol.Coerce(float),
        vol.Required(
            "storm_precipitation_trend_threshold",
            default=config.storm_precipitation_trend_threshold,
        ): vol.Coerce(float),
        vol.Required(
            "storm_wind_trend_threshold", default=config.storm_wind_trend_threshold
        ): vol.Coerce(float),
        vol.Required(
            "storm_pressure_drop_threshold", default=config.storm_pressure_drop_threshold
        ): vol.Coerce(float),
        vol.Required("storm_required_signals", default=config.storm_required_signals): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=5)
        ),
        vol.Required("apply_cooldown_seconds", default=config.apply_cooldown_seconds): vol.Coerce(
            float
        ),
        vol.Required("position_tolerance", default=config.position_tolerance): vol.Coerce(float),
    }
    for profile_name in DEFAULT_PROFILE_NAMES:
        profile = config.profile(profile_name)
        fields[vol.Required(f"position_{profile_name}_normal", default=profile.normal)] = vol.All(
            vol.Coerce(float), vol.Range(min=0, max=100)
        )
        fields[vol.Required(f"position_{profile_name}_inverted", default=profile.inverted)] = (
            vol.All(vol.Coerce(float), vol.Range(min=0, max=100))
        )
    return vol.Schema(fields)


def _mapping_from_form(
    user_input: Mapping[str, object], config: BlindControlConfig | None = None
) -> dict[str, object]:
    config = config or BlindControlConfig.defaults()
    persisted = config.to_mapping()
    values = {key: value for key, value in persisted.items() if key != "profiles"}
    values.update(user_input)
    profiles: dict[str, dict[str, object]] = {}
    for profile_name in DEFAULT_PROFILE_NAMES:
        profile = config.profile(profile_name)
        profiles[profile_name] = {
            "normal": values.pop(f"position_{profile_name}_normal", profile.normal),
            "inverted": values.pop(f"position_{profile_name}_inverted", profile.inverted),
        }
    values["profiles"] = profiles
    return values


class BlindControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create one ConfigEntry that evaluates only in Shadow mode."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            try:
                config = BlindControlConfig.from_mapping(_mapping_from_form(user_input))
            except (TypeError, ValueError, KeyError):
                return self.async_show_form(
                    step_id="user",
                    data_schema=_config_schema(),
                    errors={"base": "invalid_configuration"},
                )
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Blind Control", data=config.to_mapping())

        return self.async_show_form(step_id="user", data_schema=_config_schema())

    @staticmethod
    def async_get_options_flow(config_entry):
        return BlindControlOptionsFlow(config_entry)


class BlindControlOptionsFlow(OptionsFlow):
    """Edit profiles and calibration defaults without touching an actuator."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = BlindControlConfig.from_mapping(
            {**getattr(self._entry, "data", {}), **getattr(self._entry, "options", {})}
        )
        if user_input is not None:
            try:
                config = BlindControlConfig.from_mapping(_mapping_from_form(user_input, current))
            except (TypeError, ValueError, KeyError):
                return self.async_show_form(
                    step_id="init",
                    data_schema=_config_schema(current),
                    errors={"base": "invalid_configuration"},
                )
            return self.async_create_entry(title="", data=config.to_mapping())
        return self.async_show_form(step_id="init", data_schema=_config_schema(current))
