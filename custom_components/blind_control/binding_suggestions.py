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

    blind_master = _best(states, _is_blind_master, _blind_master_rank)
    sources = _attributes(blind_master).get("source_entities", {}) if blind_master else {}
    if not isinstance(sources, Mapping):
        sources = {}

    def suggest_from_source(key: str, *tokens: str, predicate=None) -> None:
        for entity_id in _source_entities(sources, *tokens):
            state = by_id.get(entity_id)
            if state is not None and (predicate is None or predicate(state)):
                input_suggestions[key] = entity_id
                return

    suggest_from_source("bio_state", "bio")
    suggest_from_source("activity_state", "activity")
    suggest_from_source("day_state", "day_state")
    suggest_from_source("day_context", "day_context")
    suggest_from_source("away", "presence", "away")
    suggest_from_source("private_time", "private_time")
    suggest_from_source("opening_state", "opening", predicate=_is_opening_contract)
    suggest_from_source(
        "cover_ready", "cover_ready", "readiness", "ready", predicate=_is_cover_readiness
    )
    suggest_from_source("outdoor_lux", "lux", predicate=_is_lux_contract)
    suggest_from_source("sun_elevation", "sun", predicate=_is_sun_contract)
    suggest_from_source("sun_azimuth", "sun", predicate=_is_sun_contract)
    suggest_from_source(
        "indoor_temperature",
        "indoor_temperature",
        "indoor_temp",
        predicate=_is_indoor_temperature_contract,
    )
    suggest_from_source(
        "outdoor_temperature",
        "outdoor_temperature",
        "outdoor_temp",
        "weather",
        predicate=_is_weather_contract,
    )

    activity = _state_for_suggestion(input_suggestions.get("activity_state"), by_id) or _best(
        states, _is_core_activity, _core_activity_rank
    )
    presence = _state_for_suggestion(input_suggestions.get("away"), by_id) or _best(
        states, _is_presence_contract, _presence_rank
    )
    day_state = _state_for_suggestion(input_suggestions.get("day_state"), by_id) or _best(
        states, _is_canonical_day_state, _day_state_rank
    )
    day_context = _state_for_suggestion(input_suggestions.get("day_context"), by_id) or _best(
        states, _is_day_context, _day_context_rank
    )
    bio = _state_for_suggestion(input_suggestions.get("bio_state"), by_id) or _best(
        states, _is_bio_state, _bio_state_rank
    )
    _suggest_state(input_suggestions, "activity_state", activity)
    private_time = _state_for_suggestion(input_suggestions.get("private_time"), by_id) or _best(
        states, _is_private_time_contract, _private_time_rank
    )
    _suggest_state(input_suggestions, "private_time", private_time)
    _suggest_state(input_suggestions, "away", presence)
    _suggest_state(input_suggestions, "day_state", day_state)
    _suggest_state(input_suggestions, "day_context", day_context)
    _suggest_state(input_suggestions, "bio_state", bio)

    # Privacy is derived from day_state; do not suggest retired Combined candidates.

    opening = _state_for_suggestion(input_suggestions.get("opening_state"), by_id) or _best(
        states, _is_opening_contract, _opening_rank
    )
    _suggest_state(input_suggestions, "opening_state", opening)

    opening_safety = _best(states, _is_opening_safety_contract, _opening_safety_rank)
    _suggest_state(input_suggestions, "opening_safe_for_blind", opening_safety)

    cover = _cover_from_sources(sources, by_id) or _best(
        states, _is_standard_cover, _standard_cover_rank
    )
    _suggest_state(input_suggestions, "cover_available", cover)
    _suggest_state(input_suggestions, "cover_position", cover)

    readiness = _state_for_suggestion(input_suggestions.get("cover_ready"), by_id) or _best(
        states, _is_cover_readiness, _cover_readiness_rank
    )
    _suggest_state(input_suggestions, "cover_ready", readiness)

    lux = _state_for_suggestion(input_suggestions.get("outdoor_lux"), by_id) or _best(
        states, _is_lux_contract, _lux_rank
    )
    _suggest_state(input_suggestions, "outdoor_lux", lux)

    sun = _state_for_suggestion(input_suggestions.get("sun_elevation"), by_id) or _best(
        states, _is_sun_contract, _sun_rank
    )
    _suggest_state(input_suggestions, "sun_elevation", sun)
    _suggest_state(input_suggestions, "sun_azimuth", sun)

    indoor_temperature = _state_for_suggestion(
        input_suggestions.get("indoor_temperature"), by_id
    ) or _best(states, _is_indoor_temperature_contract, _indoor_temperature_rank)
    _suggest_state(input_suggestions, "indoor_temperature", indoor_temperature)

    weather = _weather_from_sources(sources, by_id) or _best(
        states, _is_weather_contract, _weather_rank
    )
    _suggest_state(input_suggestions, "outdoor_temperature", weather)
    if weather and _has_numeric_attribute(weather, "cloud_coverage", "cloud_cover"):
        _suggest_state(input_suggestions, "cloud_cover", weather)

    legacy = _best(states, _is_legacy_debug_contract, _legacy_rank)
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


def _best(states: Iterable[object], predicate, rank) -> object | None:
    """Choose a contract deterministically, independent of HA state order."""

    candidates = [state for state in states if predicate(state)]
    return (
        min(candidates, key=lambda state: (-rank(state), _entity_id(state))) if candidates else None
    )


def _state_for_suggestion(entity_id: str | None, by_id: Mapping[str, object]) -> object | None:
    return by_id.get(entity_id) if entity_id else None


def _source_entity(sources: Mapping[object, object], *tokens: str) -> str:
    return next(iter(_source_entities(sources, *tokens)), "")


def _source_entities(sources: Mapping[object, object], *tokens: str) -> tuple[str, ...]:
    """Return source bindings by exact role/slug precedence and stable ID tie-break."""

    ranked: list[tuple[int, str]] = []
    for role, value in sources.items():
        if not isinstance(value, str):
            continue
        score = _role_score(role, tokens)
        if score:
            ranked.append((score, value))
    return tuple(value for _score, value in sorted(ranked, key=lambda item: (-item[0], item[1])))


def _role_score(role: object, tokens: tuple[str, ...]) -> int:
    normalized = _slug(role)
    without_source = normalized.removeprefix("source_")
    best = 0
    for token in tokens:
        expected = _slug(token)
        if normalized == expected or without_source == expected:
            best = max(best, 1000)
        elif normalized == f"source_{expected}" or without_source.endswith(f"_{expected}"):
            best = max(best, 900)
        elif expected in without_source.split("_"):
            best = max(best, 700)
    return best


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
    result.update(
        {key: value for key, value in current.items() if intents.get(key) != BINDING_INTENT_EMPTY}
    )
    return result


def _is_bio_state(state: object) -> bool:
    return {"sleep", "provisional_sleep", "waking", "awake"}.issubset(
        set(_attributes(state).get("options", ()))
    )


def _is_blind_master(state: object) -> bool:
    attributes = _attributes(state)
    return attributes.get("kind") == "master" and all(
        key in attributes for key in ("current_cover_position", "cover_available", "opening_state")
    )


def _is_presence_contract(state: object) -> bool:
    attributes = _attributes(state)
    return (
        "away_gate" in attributes
        or _slug(attributes.get("slug")) in {"presence", "presence_household", "presence_away"}
        or _slug(attributes.get("role")) in {"presence", "away"}
    )


def _is_core_activity(state: object) -> bool:
    attributes = _attributes(state)
    return "pc_active" in attributes and (
        "activity_decision" in attributes or "entertainment_active" in attributes
    )


def _is_private_time_contract(state: object) -> bool:
    attributes = _attributes(state)
    return (
        _state_value(state) == "private_time"
        or "private_time" in attributes
        or "private" in attributes
    )


def _is_privacy_contract(state: object) -> bool:
    """Require a dedicated boolean privacy signal, not a generic blind master."""

    attributes = _attributes(state)
    slug = _slug(attributes.get("slug"))
    role = _slug(attributes.get("role"))
    derived = attributes.get("derived")
    derived_privacy_contract = (
        slug.endswith("_privacy_candidate")
        and _slug(attributes.get("output_type")) == "boolean"
        and isinstance(derived, Mapping)
        and isinstance(derived.get("privacy"), bool)
        and _explicitly_not_degraded(attributes)
    )
    dedicated = slug in {"privacy", "privacy_candidate", "privacy_contract"} or role in {
        "privacy",
        "privacy_candidate",
        "privacy_contract",
    }
    candidate_attribute = "privacy_candidate" in attributes and _is_boolean_like(
        attributes["privacy_candidate"]
    )
    if attributes.get("kind") == "master" and not dedicated:
        return derived_privacy_contract
    return (
        dedicated
        or derived_privacy_contract
        or candidate_attribute
        or (_entity_id(state).split(".", 1)[0] == "binary_sensor" and dedicated)
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


def _is_opening_safety_contract(state: object) -> bool:
    attributes = _attributes(state)
    return _slug(attributes.get("slug")) in {
        "opening_unsafe_for_rollo",
        "opening_safe_for_blind",
    }


def _is_standard_cover(state: object) -> bool:
    return _entity_id(state).split(".", 1)[0] == "cover" and _has_numeric_attribute(
        state, "current_position"
    )


def _cover_from_sources(
    sources: Mapping[object, object], by_id: Mapping[str, object]
) -> object | None:
    for token in ("cover_position", "cover_state", "cover"):
        for entity_id in _source_entities(sources, token):
            state = _state_for_suggestion(entity_id, by_id)
            if state is not None and _is_standard_cover(state):
                return state
    return None


def _is_cover_readiness(state: object) -> bool:
    attributes = _attributes(state)
    return (
        all(
            key in attributes
            for key in ("cover_available", "current_position", "policy_context_ready")
        )
        and _is_boolean_like(attributes["cover_available"])
        and _is_boolean_like(attributes["policy_context_ready"])
        and _is_number(attributes["current_position"])
    )


def _is_lux_contract(state: object) -> bool:
    attributes = _attributes(state)
    return (attributes.get("variant") == "lux" and _is_number(getattr(state, "state", None))) or (
        attributes.get("device_class") == "illuminance"
        and _is_number(getattr(state, "state", None))
    )


def _is_sun_contract(state: object) -> bool:
    attributes = _attributes(state)
    return all(
        name in attributes and _is_number(attributes[name]) for name in ("elevation", "azimuth")
    )


def _is_indoor_temperature_contract(state: object) -> bool:
    attributes = _attributes(state)
    slug = _slug(attributes.get("slug"))
    role = _slug(attributes.get("role"))
    return _has_numeric_attribute(state, "temperature", "current_temperature") and (
        _contains_contract_token(slug, "indoor_temperature", "room_temperature", "room")
        or _contains_contract_token(role, "indoor_temperature", "room_temperature", "room")
        or (
            attributes.get("kind") == "master"
            and _contains_contract_token(
                slug,
                "climate_indoor",
                "climate_living",
                "indoor_climate",
                "room_climate",
            )
        )
        or (
            attributes.get("device_class") == "temperature"
            and _contains_contract_token(str(attributes.get("measurement", "")), "indoor", "room")
        )
    )


def _weather_from_sources(
    sources: Mapping[object, object], by_id: Mapping[str, object]
) -> object | None:
    for entity_id in _source_entities(sources, "weather", "outdoor_temperature"):
        state = _state_for_suggestion(entity_id, by_id)
        if state is not None and _is_weather_contract(state):
            return state
    return None


def _is_weather_contract(state: object) -> bool:
    attributes = _attributes(state)
    domain = _entity_id(state).split(".", 1)[0]
    return (
        _has_numeric_attribute(state, "outdoor_temperature")
        or (domain == "weather" and _has_numeric_attribute(state, "temperature"))
        or (
            attributes.get("atomic_class") == "environment"
            and _is_number(getattr(state, "state", None))
            and "temperature" in str(attributes.get("variant", ""))
        )
    )


def _has_numeric_attribute(state: object, *names: str) -> bool:
    attributes = _attributes(state)
    return any(name in attributes and _is_number(attributes[name]) for name in names)


def _is_boolean_like(value: object) -> bool:
    if isinstance(value, bool):
        return True
    return str(value).strip().lower() in {"on", "off", "true", "false", "yes", "no", "1", "0"}


def _explicitly_not_degraded(attributes: Mapping[str, object]) -> bool:
    value = attributes.get("degraded")
    if value is None:
        return True
    return str(value).strip().lower() in {"false", "off", "no", "0"}


def _slug(value: object) -> str:
    return "_".join(str(value or "").strip().lower().replace("-", "_").split())


def _contains_contract_token(value: str, *tokens: str) -> bool:
    normalized = _slug(value)
    return any(normalized == _slug(token) or _slug(token) in normalized for token in tokens)


def _rank_from_slug(state: object, *exact: str) -> int:
    attributes = _attributes(state)
    slug = _slug(attributes.get("slug"))
    role = _slug(attributes.get("role"))
    contract = _slug(attributes.get("contract"))
    if slug in {_slug(value) for value in exact}:
        return 1000
    if role in {_slug(value) for value in exact}:
        return 900
    if contract in {_slug(value) for value in exact}:
        return 800
    return 0


def _blind_master_rank(state: object) -> int:
    return _rank_from_slug(state, "blind", "living_blind", "blind_master")


def _bio_state_rank(state: object) -> int:
    return _rank_from_slug(state, "bio_state", "bio")


def _core_activity_rank(state: object) -> int:
    return _rank_from_slug(state, "activity_state", "activity") + (
        100 if "activity_decision" in _attributes(state) else 0
    )


def _presence_rank(state: object) -> int:
    return _rank_from_slug(state, "presence", "presence_household", "presence_away") + (
        100 if "away_gate" in _attributes(state) else 0
    )


def _private_time_rank(state: object) -> int:
    return _rank_from_slug(state, "private_time", "private_time_candidate") + (
        100 if "private_time" in _attributes(state) else 0
    )


def _privacy_rank(state: object) -> int:
    attributes = _attributes(state)
    slug = _slug(attributes.get("slug"))
    derived = attributes.get("derived")
    if (
        slug.endswith("_privacy_candidate")
        and _slug(attributes.get("output_type")) == "boolean"
        and isinstance(derived, Mapping)
        and isinstance(derived.get("privacy"), bool)
        and _explicitly_not_degraded(attributes)
    ):
        return 1400
    return _rank_from_slug(state, "privacy", "privacy_candidate", "privacy_contract") + (
        100 if "privacy_candidate" in _attributes(state) else 0
    )


def _day_state_rank(state: object) -> int:
    return _rank_from_slug(state, "day_state", "day")


def _day_context_rank(state: object) -> int:
    return _rank_from_slug(state, "day_context", "calendar_context")


def _opening_rank(state: object) -> int:
    return _rank_from_slug(state, "opening", "opening_state", "opening_contract")


def _opening_safety_rank(state: object) -> int:
    return _rank_from_slug(state, "opening_unsafe_for_rollo", "opening_safe_for_blind")


def _standard_cover_rank(state: object) -> int:
    return _rank_from_slug(state, "cover", "cover_position", "blind")


def _cover_readiness_rank(state: object) -> int:
    return _rank_from_slug(state, "cover_ready", "technical_readiness", "readiness")


def _lux_rank(state: object) -> int:
    return _rank_from_slug(state, "outdoor_lux", "lux", "illuminance") + (
        100 if _attributes(state).get("device_class") == "illuminance" else 0
    )


def _sun_rank(state: object) -> int:
    return _rank_from_slug(state, "sun", "sun_geometry") + (
        100 if _entity_id(state).split(".", 1)[0] == "sun" else 0
    )


def _indoor_temperature_rank(state: object) -> int:
    return _rank_from_slug(state, "indoor_temperature", "room_temperature", "climate_indoor") + (
        100 if _attributes(state).get("device_class") == "temperature" else 0
    )


def _weather_rank(state: object) -> int:
    return _rank_from_slug(state, "outdoor_temperature", "weather_environment", "weather") + (
        200 if _entity_id(state).split(".", 1)[0] == "weather" else 0
    )


def _legacy_rank(state: object) -> int:
    return _rank_from_slug(state, "legacy_debug", "shadow_status")


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
