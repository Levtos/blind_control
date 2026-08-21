"""ConfigEntry and OptionsFlow for the non-actuating AP2 shadow runtime."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector

from .binding_suggestions import BindingSuggestions, discover_binding_suggestions
from .config import (
    BINDING_GROUPS,
    BINDING_INTENT_BOUND,
    BINDING_INTENT_EMPTY,
    CONDITIONAL_BINDING_KEYS,
    DEFAULT_PROFILE_NAMES,
    MANDATORY_AUTOMATIC_BINDING_KEYS,
    MANDATORY_TECHNICAL_BINDING_KEYS,
    OPENING_SAFETY_POLARITIES,
    BlindControlConfig,
)
from .const import DOMAIN
from .open_meteo import OpenMeteoUrlError, suggested_open_meteo_url


def _config_schema(
    config: BlindControlConfig | None = None,
    suggestions: BindingSuggestions | None = None,
    open_meteo_suggestion: str = "",
):
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
        vol.Required(
            "open_meteo_api_url",
            default=config.open_meteo_api_url or open_meteo_suggestion,
        ): selector({"text": {"type": "url"}}),
        vol.Required(
            "observation_freshness_seconds", default=config.observation_freshness_seconds
        ): vol.All(vol.Coerce(float), vol.Range(min=1, max=86400)),
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
        vol.Required(
            "glare_confidence_threshold", default=config.glare_confidence_threshold
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
    input_bindings = dict(config.input_bindings)
    legacy_bindings = dict(config.legacy_bindings)
    suggested_input = dict(suggestions.input_bindings) if suggestions else {}
    suggested_legacy = dict(suggestions.legacy_bindings) if suggestions else {}
    for section_key, _label, keys, legacy in BINDING_GROUPS:
        bindings = legacy_bindings if legacy else input_bindings
        suggested_bindings = suggested_legacy if legacy else suggested_input
        binding_fields: dict[object, object] = {}
        section_defaults: dict[str, str] = {}
        for key in keys:
            field_kwargs: dict[str, object] = {}
            suggested_value = _binding_form_value(
                config,
                bindings,
                suggested_bindings,
                key,
            )
            if suggested_value:
                field_kwargs["description"] = {"suggested_value": suggested_value}
                if key in bindings or _should_prefill_binding(key, legacy):
                    field_kwargs["default"] = suggested_value
                    section_defaults[key] = suggested_value
            binding_fields[vol.Optional(key, **field_kwargs)] = selector({"entity": {}})
        if section_key == "opening_safety_cover_bindings":
            polarity = (
                config.opening_safety_polarity
                if config.opening_safety_polarity != "unspecified"
                else (suggestions.opening_safety_polarity if suggestions else None) or "unspecified"
            )
            binding_fields[
                vol.Required(
                    "opening_safety_polarity",
                    default=polarity,
                )
            ] = selector(
                {
                    "select": {
                        "options": list(OPENING_SAFETY_POLARITIES),
                        "mode": "dropdown",
                        "translation_key": "opening_safety_polarity",
                    }
                }
            )
            if polarity != "unspecified":
                section_defaults["opening_safety_polarity"] = polarity
        fields[vol.Required(section_key, default=section_defaults)] = section(
            vol.Schema(binding_fields),
            {"collapsed": True},
        )
    return vol.Schema(fields)


def _binding_form_value(
    config: BlindControlConfig,
    bindings: Mapping[str, str],
    suggestions: Mapping[str, str],
    key: str,
) -> str | None:
    """Return a binding for the form while respecting an explicit empty intent."""

    if dict(config.binding_intents).get(key) == BINDING_INTENT_EMPTY:
        return None
    return bindings.get(key, suggestions.get(key))


def _should_prefill_binding(key: str, legacy: bool) -> bool:
    """Only auto-bind required/conditional owner contracts; optionals stay suggestions."""

    return not legacy and (
        key in MANDATORY_AUTOMATIC_BINDING_KEYS
        or key in MANDATORY_TECHNICAL_BINDING_KEYS
        or key in CONDITIONAL_BINDING_KEYS
    )


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
    input_bindings = dict(config.input_bindings)
    legacy_bindings = dict(config.legacy_bindings)
    binding_intents = dict(config.binding_intents)
    for key, intent in binding_intents.items():
        if intent == BINDING_INTENT_EMPTY:
            input_bindings.pop(key, None)
            legacy_bindings.pop(key, None)
    for section_key, _label, keys, legacy in BINDING_GROUPS:
        raw_section = values.pop(section_key, {})
        if raw_section is None:
            raw_section = {}
        if not isinstance(raw_section, Mapping):
            raise ValueError(f"{section_key} must be a mapping")
        bindings = legacy_bindings if legacy else input_bindings
        if section_key == "opening_safety_cover_bindings":
            values["opening_safety_polarity"] = raw_section.get(
                "opening_safety_polarity",
                config.opening_safety_polarity,
            )
        for key in keys:
            if key not in raw_section:
                continue
            value = raw_section[key]
            if value in (None, ""):
                bindings.pop(key, None)
                binding_intents[key] = BINDING_INTENT_EMPTY
            else:
                bindings[key] = value
                binding_intents[key] = BINDING_INTENT_BOUND
    values["input_bindings"] = input_bindings
    values["legacy_bindings"] = legacy_bindings
    values["binding_intents"] = binding_intents
    values["profiles"] = profiles
    return values


class BlindControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create one ConfigEntry that evaluates only in Shadow mode."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        open_meteo_suggestion = _suggested_provider_url(getattr(self, "hass", None))
        suggestions = discover_binding_suggestions(
            getattr(self, "hass", None), BlindControlConfig.defaults()
        )
        if user_input is not None:
            try:
                config = BlindControlConfig.from_mapping(_mapping_from_form(user_input))
            except OpenMeteoUrlError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=_config_schema(
                        suggestions=suggestions,
                        open_meteo_suggestion=str(
                            user_input.get("open_meteo_api_url", open_meteo_suggestion)
                        ),
                    ),
                    errors={"open_meteo_api_url": "invalid_open_meteo_url"},
                )
            except (TypeError, ValueError, KeyError):
                return self.async_show_form(
                    step_id="user",
                    data_schema=_config_schema(
                        suggestions=suggestions,
                        open_meteo_suggestion=open_meteo_suggestion,
                    ),
                    errors={"base": "invalid_configuration"},
                )
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Blind Control", data=config.to_mapping())

        return self.async_show_form(
            step_id="user",
            data_schema=_config_schema(
                suggestions=suggestions,
                open_meteo_suggestion=open_meteo_suggestion,
            ),
        )

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
        suggestions = discover_binding_suggestions(getattr(self, "hass", None), current)
        open_meteo_suggestion = current.open_meteo_api_url or _suggested_provider_url(
            getattr(self, "hass", None)
        )
        if user_input is not None:
            try:
                config = BlindControlConfig.from_mapping(_mapping_from_form(user_input, current))
            except OpenMeteoUrlError:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_config_schema(
                        current,
                        suggestions,
                        str(user_input.get("open_meteo_api_url", open_meteo_suggestion)),
                    ),
                    errors={"open_meteo_api_url": "invalid_open_meteo_url"},
                )
            except (TypeError, ValueError, KeyError):
                return self.async_show_form(
                    step_id="init",
                    data_schema=_config_schema(current, suggestions, open_meteo_suggestion),
                    errors={"base": "invalid_configuration"},
                )
            return self.async_create_entry(title="", data=config.to_mapping())
        return self.async_show_form(
            step_id="init",
            data_schema=_config_schema(current, suggestions, open_meteo_suggestion),
        )


def _suggested_provider_url(hass: object | None) -> str:
    """Suggest a private URL only inside the native form, never diagnostics."""

    config = getattr(hass, "config", None)
    latitude = getattr(config, "latitude", None)
    longitude = getattr(config, "longitude", None)
    if latitude is None or longitude is None:
        return ""
    return suggested_open_meteo_url(
        latitude,
        longitude,
        getattr(config, "time_zone", "UTC"),
    )
