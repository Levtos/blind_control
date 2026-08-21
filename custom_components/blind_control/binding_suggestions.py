"""Small installation-local binding suggestions derived from HA contracts.

This module deliberately discovers existing entities by their published state and
attribute contracts.  It is not a registry and contains no installation-specific
entity IDs.  Suggestions are only presented in the native OptionsFlow; persisted
user choices and explicit empty intents always win.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .config import BINDING_INTENT_EMPTY, BlindControlConfig


@dataclass(frozen=True, slots=True)
class BindingSuggestions:
    """Suggested bindings and polarity for one current HA installation."""

    input_bindings: Mapping[str, str]
    legacy_bindings: Mapping[str, str]
    opening_safety_polarity: str | None = None


def discover_binding_suggestions(hass: object, config: BlindControlConfig) -> BindingSuggestions:
    """Discover the smallest contract-compatible prefill from current HA states."""

    states = tuple(_all_states(hass))
    by_id = {_entity_id(state): state for state in states if _entity_id(state)}
    input_suggestions: dict[str, str] = {}
    legacy_suggestions: dict[str, str] = {}

    blind_master = _first(
        states,
        lambda state: (
            _attributes(state).get("kind") == "master"
            and all(
                key in _attributes(state)
                for key in ("current_cover_position", "cover_available", "opening_state")
            )
        ),
    )
    sources = _attributes(blind_master).get("source_entities", {}) if blind_master else {}
    if not isinstance(sources, Mapping):
        sources = {}

    def suggest_from_source(key: str, *tokens: str) -> None:
        entity_id = _source_entity(sources, *tokens)
        if entity_id in by_id:
            input_suggestions[key] = entity_id

    suggest_from_source("bio_state", "bio")
    suggest_from_source("activity_state", "activity")
    suggest_from_source("day_state", "day_state")
    suggest_from_source("day_context", "day_context")
    suggest_from_source("away", "presence", "away")
    suggest_from_source("opening_state", "opening")
    suggest_from_source("outdoor_lux", "lux")
    suggest_from_source("sun_elevation", "sun")
    suggest_from_source("sun_azimuth", "sun")

    activity = _state_for_suggestion(input_suggestions.get("activity_state"), by_id) or _first(
        states, _is_core_activity
    )
    presence = _state_for_suggestion(input_suggestions.get("away"), by_id) or _first(
        states, lambda state: "away_gate" in _attributes(state)
    )
    day_state = _state_for_suggestion(input_suggestions.get("day_state"), by_id) or _first(
        states, _is_canonical_day_state
    )
    day_context = _state_for_suggestion(input_suggestions.get("day_context"), by_id) or _first(
        states, _is_day_context
    )
    bio = _state_for_suggestion(input_suggestions.get("bio_state"), by_id) or _first(
        states, _is_bio_state
    )
    _suggest_state(input_suggestions, "activity_state", activity)
    _suggest_state(input_suggestions, "private_time", activity)
    _suggest_state(input_suggestions, "away", presence)
    _suggest_state(input_suggestions, "day_state", day_state)
    _suggest_state(input_suggestions, "day_context", day_context)
    _suggest_state(input_suggestions, "bio_state", bio)

    privacy = _first(
        states,
        lambda state: (
            "privacy_candidate" in _attributes(state)
            or _attributes(state).get("slug") == "privacy_candidate"
        ),
    )
    _suggest_state(input_suggestions, "privacy", privacy)

    opening = _state_for_suggestion(input_suggestions.get("opening_state"), by_id) or _first(
        states, _is_opening_contract
    )
    _suggest_state(input_suggestions, "opening_state", opening)

    opening_safety = _first(
        states,
        lambda state: _attributes(state).get("slug") == "opening_unsafe_for_rollo",
    )
    _suggest_state(input_suggestions, "opening_safe_for_blind", opening_safety)

    cover = _cover_from_sources(sources, by_id) or _first(states, _is_standard_cover)
    _suggest_state(input_suggestions, "cover_available", cover)
    _suggest_state(input_suggestions, "cover_position", cover)

    readiness = _first(states, _is_cover_readiness)
    _suggest_state(input_suggestions, "cover_ready", readiness)

    lux = _state_for_suggestion(input_suggestions.get("outdoor_lux"), by_id) or _first(
        states, _is_lux_contract
    )
    _suggest_state(input_suggestions, "outdoor_lux", lux)

    sun = _state_for_suggestion(input_suggestions.get("sun_elevation"), by_id) or _first(
        states, _is_sun_contract
    )
    _suggest_state(input_suggestions, "sun_elevation", sun)
    _suggest_state(input_suggestions, "sun_azimuth", sun)

    indoor_temperature = _first(states, _is_indoor_temperature_contract)
    _suggest_state(input_suggestions, "indoor_temperature", indoor_temperature)

    weather = _weather_from_sources(sources, by_id) or _first(states, _is_weather_contract)
    _suggest_state(input_suggestions, "outdoor_temperature", weather)
    if weather and _has_numeric_attribute(weather, "cloud_coverage", "cloud_cover"):
        _suggest_state(input_suggestions, "cloud_cover", weather)

    for field, marker in (
        ("expected_direct_radiation", "direct_normal_irradiance_instant"),
        ("expected_diffuse_radiation", "diffuse_radiation_instant"),
    ):
        _suggest_state(
            input_suggestions,
            field,
            _first(states, lambda state, marker=marker: _has_contract_marker(state, marker)),
        )

    legacy = _first(states, _is_legacy_debug_contract)
    if legacy is not None:
        entity_id = _entity_id(legacy)
        legacy_suggestions.update(
            {
                key: entity_id
                for key in ("active_mode", "effective_target", "safety_status", "apply_status")
            }
        )

    current_input = dict(config.input_bindings)
    current_legacy = dict(config.legacy_bindings)
    intents = dict(config.binding_intents)
    input_suggestions = _apply_user_precedence(input_suggestions, current_input, intents)
    legacy_suggestions = _apply_user_precedence(legacy_suggestions, current_legacy, intents)
    polarity = "negative_unsafe" if opening_safety is not None else None
    if config.opening_safety_polarity != "unspecified":
        polarity = config.opening_safety_polarity
    return BindingSuggestions(input_suggestions, legacy_suggestions, polarity)


def _all_states(hass: object) -> Iterable[object]:
    state_machine = getattr(hass, "states", None)
    async_all = getattr(state_machine, "async_all", None)
    if not callable(async_all):
        return ()
    return async_all()


def _entity_id(state: object | None) -> str:
    return str(getattr(state, "entity_id", "")) if state is not None else ""


def _attributes(state: object | None) -> Mapping[str, object]:
    attributes = getattr(state, "attributes", {}) if state is not None else {}
    return attributes if isinstance(attributes, Mapping) else {}


def _state_value(state: object) -> str:
    return str(getattr(state, "state", "")).strip().lower()


def _first(states: Iterable[object], predicate) -> object | None:
    return next((state for state in states if predicate(state)), None)


def _state_for_suggestion(entity_id: str | None, by_id: Mapping[str, object]) -> object | None:
    return by_id.get(entity_id) if entity_id else None


def _source_entity(sources: Mapping[object, object], *tokens: str) -> str:
    for role, value in sources.items():
        normalized_role = str(role).lower()
        if any(token in normalized_role for token in tokens) and isinstance(value, str):
            return value
    return ""


def _suggest_state(suggestions: dict[str, str], key: str, state: object | None) -> None:
    entity_id = _entity_id(state)
    if entity_id:
        suggestions.setdefault(key, entity_id)


def _apply_user_precedence(
    suggestions: Mapping[str, str], current: Mapping[str, str], intents: Mapping[str, str]
) -> dict[str, str]:
    result = {
        key: value for key, value in suggestions.items() if intents.get(key) != BINDING_INTENT_EMPTY
    }
    result.update(current)
    return result


def _is_bio_state(state: object) -> bool:
    return {"sleep", "provisional_sleep", "waking", "awake"}.issubset(
        set(_attributes(state).get("options", ()))
    )


def _is_core_activity(state: object) -> bool:
    attributes = _attributes(state)
    return "pc_active" in attributes and (
        "activity_decision" in attributes or "entertainment_active" in attributes
    )


def _is_canonical_day_state(state: object) -> bool:
    return _state_value(state) in {
        "early_night",
        "late_night",
        "early_morning",
        "forenoon",
        "midday",
        "afternoon",
        "late_afternoon",
        "evening",
        "late_evening",
    }


def _is_day_context(state: object) -> bool:
    return _state_value(state) in {"werktag", "wochenende", "frei", "weekday", "weekend", "holiday"}


def _is_opening_contract(state: object) -> bool:
    return _state_value(state) in {"closed", "open", "tilted"} and (
        _attributes(state).get("kind") == "master" or "unsafe_for_rollo" in _attributes(state)
    )


def _is_standard_cover(state: object) -> bool:
    return _entity_id(state).split(".", 1)[0] == "cover" and "current_position" in _attributes(
        state
    )


def _cover_from_sources(
    sources: Mapping[object, object], by_id: Mapping[str, object]
) -> object | None:
    for token in ("cover_position", "cover_state", "cover"):
        state = _state_for_suggestion(_source_entity(sources, token), by_id)
        if state is not None and _is_standard_cover(state):
            return state
    return None


def _is_cover_readiness(state: object) -> bool:
    attributes = _attributes(state)
    return all(
        key in attributes for key in ("cover_available", "current_position", "policy_context_ready")
    )


def _is_lux_contract(state: object) -> bool:
    attributes = _attributes(state)
    return attributes.get("variant") == "lux" and _is_number(getattr(state, "state", None))


def _is_sun_contract(state: object) -> bool:
    return _has_numeric_attribute(state, "elevation", "azimuth")


def _is_indoor_temperature_contract(state: object) -> bool:
    attributes = _attributes(state)
    slug = str(attributes.get("slug", ""))
    return (
        attributes.get("kind") == "master"
        and "climate" in slug
        and _has_numeric_attribute(state, "temperature")
    )


def _weather_from_sources(
    sources: Mapping[object, object], by_id: Mapping[str, object]
) -> object | None:
    return _state_for_suggestion(_source_entity(sources, "weather", "outdoor_temperature"), by_id)


def _is_weather_contract(state: object) -> bool:
    attributes = _attributes(state)
    return _has_numeric_attribute(state, "outdoor_temperature") or (
        attributes.get("atomic_class") == "environment"
        and _is_number(getattr(state, "state", None))
        and "temperature" in str(attributes.get("variant", ""))
    )


def _has_numeric_attribute(state: object, *names: str) -> bool:
    attributes = _attributes(state)
    return any(name in attributes and _is_number(attributes[name]) for name in names)


def _has_contract_marker(state: object, marker: str) -> bool:
    attributes = _attributes(state)
    return (
        marker in attributes
        or attributes.get("blind_control_evidence") == marker
        or attributes.get("contract_field") == marker
    )


def _is_legacy_debug_contract(state: object) -> bool:
    attributes = _attributes(state)
    return all(
        key in attributes for key in ("active_mode", "active_position", "apply_enabled", "blockers")
    )


def _is_number(value: object) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
