"""Validated, serializable Blind Control configuration defaults."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .open_meteo import normalize_open_meteo_url

CONFIG_VERSION = 6

RUNTIME_MODES = ("shadow", "live")
APPLY_OWNERS = ("legacy", "blind_control")

BINDING_INTENT_BOUND = "bound"
BINDING_INTENT_EMPTY = "intentionally_empty"
BINDING_INTENTS = frozenset({BINDING_INTENT_BOUND, BINDING_INTENT_EMPTY})

OPENING_SAFETY_POLARITIES = (
    "unspecified",
    "positive_safe",
    "negative_unsafe",
)

INPUT_BINDING_KEYS = (
    "bio_state",
    "activity_state",
    "day_state",
    "day_context",
    "away",
    "private_time",
    "privacy",
    "opening_state",
    "opening_safe_for_blind",
    "cover_available",
    "cover_ready",
    "cover_position",
    "outdoor_lux",
    "lux_trend",
    "sun_elevation",
    "sun_azimuth",
    "expected_direct_radiation",
    "expected_diffuse_radiation",
    "cloud_cover",
    "indoor_temperature",
    "outdoor_temperature",
    "indoor_temperature_trend",
    "outdoor_temperature_trend",
    "weather_alert",
    "precipitation_trend",
    "wind_trend",
    "pressure_trend",
    "air_movement",
)
LEGACY_BINDING_KEYS = ("active_mode", "effective_target", "safety_status", "apply_status")
MANDATORY_AUTOMATIC_BINDING_KEYS = frozenset(
    {
        "bio_state",
        "activity_state",
        "day_state",
        "day_context",
        "away",
        "private_time",
        "privacy",
        "outdoor_lux",
        "sun_elevation",
        "sun_azimuth",
        "indoor_temperature",
        "outdoor_temperature",
    }
)
MANDATORY_TECHNICAL_BINDING_KEYS = frozenset(
    {"opening_state", "cover_available", "cover_ready", "cover_position"}
)
CONDITIONAL_BINDING_KEYS = frozenset({"opening_safe_for_blind"})
OPTIONAL_EVIDENCE_BINDING_KEYS = frozenset(INPUT_BINDING_KEYS) - (
    MANDATORY_AUTOMATIC_BINDING_KEYS | MANDATORY_TECHNICAL_BINDING_KEYS | CONDITIONAL_BINDING_KEYS
)
BINDING_GROUPS: tuple[tuple[str, str, tuple[str, ...], bool], ...] = (
    (
        "core_state_bindings",
        "Core State",
        (
            "bio_state",
            "activity_state",
            "day_state",
            "day_context",
            "away",
            "private_time",
            "privacy",
        ),
        False,
    ),
    (
        "opening_safety_cover_bindings",
        "Opening / Safety / Cover",
        (
            "opening_state",
            "opening_safe_for_blind",
            "cover_available",
            "cover_ready",
            "cover_position",
        ),
        False,
    ),
    (
        "solar_bindings",
        "Solar",
        (
            "outdoor_lux",
            "lux_trend",
            "sun_elevation",
            "sun_azimuth",
            "expected_direct_radiation",
            "expected_diffuse_radiation",
            "cloud_cover",
        ),
        False,
    ),
    (
        "temperature_weather_bindings",
        "Temperatur / Wetter",
        (
            "indoor_temperature",
            "outdoor_temperature",
            "indoor_temperature_trend",
            "outdoor_temperature_trend",
            "weather_alert",
            "precipitation_trend",
            "wind_trend",
            "pressure_trend",
            "air_movement",
        ),
        False,
    ),
    (
        "legacy_comparison_bindings",
        "Legacy-Vergleich",
        LEGACY_BINDING_KEYS,
        True,
    ),
)
STATEFUL_BINDING_KEYS = frozenset(
    {
        "bio_state",
        "activity_state",
        "day_state",
        "day_context",
        "away",
        "private_time",
        "privacy",
    }
)
SAFETY_STATE_BINDING_KEYS = frozenset(
    {"opening_state", "opening_safe_for_blind", "cover_available", "cover_ready"}
)
TIME_CRITICAL_BINDING_KEYS = frozenset(
    set(INPUT_BINDING_KEYS) - STATEFUL_BINDING_KEYS - SAFETY_STATE_BINDING_KEYS
)
_BINDING_OWNER_BY_KEY = {
    **dict.fromkeys(STATEFUL_BINDING_KEYS, "core_state"),
    **dict.fromkeys(SAFETY_STATE_BINDING_KEYS | {"cover_position"}, "technical_device"),
    **dict.fromkeys(
        {
            "outdoor_lux",
            "lux_trend",
            "sun_elevation",
            "sun_azimuth",
            "expected_direct_radiation",
            "expected_diffuse_radiation",
            "cloud_cover",
        },
        "solar_environment",
    ),
    **dict.fromkeys(
        {
            "indoor_temperature",
            "outdoor_temperature",
            "indoor_temperature_trend",
            "outdoor_temperature_trend",
            "weather_alert",
            "precipitation_trend",
            "wind_trend",
            "pressure_trend",
            "air_movement",
        },
        "weather_environment",
    ),
    "privacy": "privacy_owner",
    "opening_state": "opening_owner",
    "opening_safe_for_blind": "opening_owner",
    "cover_available": "cover_device",
    "cover_position": "cover_device",
    "cover_ready": "technical_readiness",
}
_ENTITY_ID = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")
_FIELD_FRESHNESS_FLOORS = {
    "outdoor_lux": 900.0,
    "lux_trend": 900.0,
    "sun_elevation": 900.0,
    "sun_azimuth": 900.0,
    "expected_direct_radiation": 1200.0,
    "expected_diffuse_radiation": 1200.0,
    "cloud_cover": 1800.0,
    "indoor_temperature": 1800.0,
    "outdoor_temperature": 1800.0,
    "indoor_temperature_trend": 1800.0,
    "outdoor_temperature_trend": 1800.0,
    "weather_alert": 1800.0,
    "precipitation_trend": 1800.0,
    "wind_trend": 1800.0,
    "pressure_trend": 1800.0,
    "air_movement": 1800.0,
}


@dataclass(frozen=True, slots=True)
class BindingFreshness:
    """Owner- and field-specific evidence policy for one bound value."""

    max_age_seconds: float | None
    require_timestamp: bool
    owner: str

    def __post_init__(self) -> None:
        if self.max_age_seconds is not None:
            _number(
                self.max_age_seconds,
                name="binding max_age_seconds",
                minimum=1,
                maximum=86_400,
            )
        if not isinstance(self.require_timestamp, bool):
            raise ValueError("binding require_timestamp must be boolean")
        if not isinstance(self.owner, str) or not self.owner.strip():
            raise ValueError("binding owner must be a non-empty string")

    def as_dict(self) -> dict[str, object]:
        return {
            "max_age_seconds": self.max_age_seconds,
            "require_timestamp": self.require_timestamp,
            "owner": self.owner,
        }


def default_binding_freshness(
    key: str,
    freshness_seconds: float,
    *,
    legacy: bool = False,
) -> BindingFreshness:
    """Return the conservative default policy for one input contract field."""

    if legacy:
        return BindingFreshness(freshness_seconds, True, "legacy_policy")
    owner = _BINDING_OWNER_BY_KEY.get(key, "unassigned")
    if key in STATEFUL_BINDING_KEYS:
        return BindingFreshness(None, False, owner)
    if key in SAFETY_STATE_BINDING_KEYS:
        return BindingFreshness(None, True, owner)
    return BindingFreshness(
        max(freshness_seconds, _FIELD_FRESHNESS_FLOORS.get(key, freshness_seconds)),
        True,
        owner,
    )


@dataclass(frozen=True, slots=True)
class PositionProfile:
    """One logical target; the device-axis complement is never editable."""

    logical: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.logical, bool)
            or not isinstance(self.logical, (int, float))
            or not 0 <= self.logical <= 100
        ):
            raise ValueError("logical position must be numeric and between 0 and 100")

    @property
    def inverted(self) -> float:
        return 100 - self.logical

    def as_dict(self) -> dict[str, float]:
        return {"logical": self.logical}


DEFAULT_PROFILES: tuple[tuple[str, PositionProfile], ...] = (
    ("window_safety", PositionProfile(100)),
    ("privacy_bed", PositionProfile(40)),
    ("waking", PositionProfile(100)),
    ("sleep", PositionProfile(5)),
    ("away", PositionProfile(5)),
    ("private_time", PositionProfile(40)),
    ("privacy", PositionProfile(40)),
    ("heat_protection", PositionProfile(15)),
    ("glare_general", PositionProfile(60)),
    ("glare_tv", PositionProfile(60)),
    ("glare_pc", PositionProfile(75)),
    ("cold_insulation", PositionProfile(5)),
    ("storm_approaching", PositionProfile(100)),
    ("cool_air_available", PositionProfile(100)),
    ("open", PositionProfile(100)),
    ("manual_override", PositionProfile(50)),
)

DEFAULT_PROFILE_NAMES = tuple(name for name, _ in DEFAULT_PROFILES)


def _profile_items(value: object) -> tuple[tuple[str, PositionProfile], ...]:
    if value is None:
        return DEFAULT_PROFILES
    if not isinstance(value, Mapping):
        raise ValueError("profiles must be a mapping")

    defaults = dict(DEFAULT_PROFILES)
    for name, raw in value.items():
        if name not in defaults:
            raise ValueError(f"unknown profile: {name}")
        if not isinstance(raw, Mapping):
            raise ValueError(f"profile {name} must be a mapping")
        defaults[name] = PositionProfile(_position(raw.get("logical", raw.get("normal"))))
    return tuple((name, defaults[name]) for name in DEFAULT_PROFILE_NAMES)


def _position(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("position must be numeric")
    return float(value)


def _number(value: object, *, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return result


def _bindings(
    value: object,
    *,
    name: str,
    allowed: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    """Validate owner-selected HA entity bindings without inventing topology."""

    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    allowed_set = set(allowed)
    result: list[tuple[str, str]] = []
    for key, entity_id in value.items():
        if key not in allowed_set:
            raise ValueError(f"unknown {name} key: {key}")
        if entity_id in (None, ""):
            continue
        if not isinstance(entity_id, str) or not _ENTITY_ID.fullmatch(entity_id):
            raise ValueError(f"{name}.{key} must be a Home Assistant entity ID")
        result.append((key, entity_id))
    return tuple(sorted(result))


def _effective_max_age(key: str, max_age: float | None) -> float | None:
    """Keep legacy persisted ages from weakening a field's safety floor."""

    floor = _FIELD_FRESHNESS_FLOORS.get(key)
    if floor is None:
        return max_age
    if max_age is None or max_age < floor:
        return floor
    return max_age


def _binding_intents(value: object) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError("binding_intents must be a mapping")
    allowed = set(INPUT_BINDING_KEYS) | set(LEGACY_BINDING_KEYS)
    result: list[tuple[str, str]] = []
    for key, raw_intent in value.items():
        if key not in allowed:
            raise ValueError(f"unknown binding_intents key: {key}")
        intent = str(raw_intent)
        if intent not in BINDING_INTENTS:
            raise ValueError(f"unsupported binding_intents value for {key}")
        result.append((key, intent))
    return tuple(sorted(result))


def _binding_freshness(
    value: object, freshness_seconds: float
) -> tuple[tuple[str, BindingFreshness], ...]:
    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError("binding_freshness must be a mapping")
    allowed = set(INPUT_BINDING_KEYS) | set(LEGACY_BINDING_KEYS)
    result: list[tuple[str, BindingFreshness]] = []
    for key, raw_policy in value.items():
        if key not in allowed:
            raise ValueError(f"unknown binding_freshness key: {key}")
        if not isinstance(raw_policy, Mapping):
            raise ValueError(f"binding_freshness.{key} must be a mapping")
        default = default_binding_freshness(
            key,
            freshness_seconds,
            legacy=key in LEGACY_BINDING_KEYS,
        )
        max_age = raw_policy.get("max_age_seconds", default.max_age_seconds)
        if max_age is not None:
            max_age = _number(
                max_age,
                name=f"binding_freshness.{key}.max_age_seconds",
                minimum=1,
                maximum=86_400,
            )
        max_age = _effective_max_age(key, max_age)
        require_timestamp = raw_policy.get("require_timestamp", default.require_timestamp)
        owner = raw_policy.get("owner", default.owner)
        result.append(
            (
                key,
                BindingFreshness(
                    max_age,
                    _bool(require_timestamp, f"binding_freshness.{key}.require_timestamp"),
                    owner,
                ),
            )
        )
    return tuple(sorted(result))


@dataclass(frozen=True, slots=True)
class BlindControlConfig:
    """All runtime-calibratable values for the deterministic shadow engine."""

    profiles: tuple[tuple[str, PositionProfile], ...] = DEFAULT_PROFILES
    legacy_profile_values: tuple[tuple[str, float, float], ...] = ()
    window_azimuth: float = 124.0
    window_tilt: float = 90.0
    axis_inverted: bool = False
    automation_enabled: bool = True
    apply_enabled: bool = True
    runtime_mode: str = "shadow"
    apply_owner: str = "legacy"
    core_contract_profile: str = "benni"
    core_contracts: tuple[tuple[str, str], ...] = ()
    open_meteo_api_url: str = ""
    opening_safety_polarity: str = "unspecified"
    input_bindings: tuple[tuple[str, str], ...] = ()
    legacy_bindings: tuple[tuple[str, str], ...] = ()
    binding_intents: tuple[tuple[str, str], ...] = ()
    observation_freshness_seconds: float = 120.0
    binding_freshness: tuple[tuple[str, BindingFreshness], ...] = ()

    heat_outdoor_threshold: float = 30.0
    heat_indoor_threshold: float = 26.0
    heat_radiation_threshold: float = 250.0
    heat_confidence_threshold: float = 0.55
    glare_confidence_threshold: float = 0.35
    cloud_shadow_lux_drop: float = 1000.0
    cloud_cover_threshold: float = 75.0
    model_lux_ratio: float = 0.75
    minimum_incidence_factor: float = 0.05
    model_lux_per_watt: float = 120.0
    diffuse_lux_threshold: float = 2500.0
    night_lux_threshold: float = 50.0
    cold_outdoor_threshold: float = 8.0
    cold_lux_enter_threshold: float = 400.0
    cold_lux_exit_threshold: float = 500.0
    environment_hysteresis_ratio: float = 0.8
    environment_enter_seconds: float = 10.0
    environment_exit_seconds: float = 120.0
    position_settle_seconds: float = 2.0
    movement_timeout_seconds: float = 120.0
    movement_recovery_seconds: float = 30.0
    cool_air_delta: float = 2.0
    storm_precipitation_trend_threshold: float = 0.0
    storm_wind_trend_threshold: float = 0.0
    storm_pressure_drop_threshold: float = 0.0
    storm_required_signals: int = 2
    apply_cooldown_seconds: float = 60.0
    position_tolerance: float = 3.0

    def __post_init__(self) -> None:
        if self.core_contract_profile not in {"benni", "eltern"}:
            raise ValueError("unsupported core contract profile")
        if len(dict(self.core_contracts)) != len(self.core_contracts):
            raise ValueError("duplicate core contract selection")
        for schema, contract_id in self.core_contracts:
            if schema not in {"opening", "room_climate", "weather_environment"}:
                raise ValueError("unsupported core contract schema")
            if (
                not isinstance(contract_id, str)
                or not contract_id.strip()
                or len(contract_id) > 160
            ):
                raise ValueError("invalid core contract selection")
        _number(self.window_azimuth, name="window_azimuth", minimum=0, maximum=360)
        _number(self.window_tilt, name="window_tilt", minimum=0, maximum=180)
        for name in ("heat_outdoor_threshold", "heat_indoor_threshold", "cold_outdoor_threshold"):
            _number(getattr(self, name), name=name, minimum=-100, maximum=100)
        for name in (
            "heat_radiation_threshold",
            "cloud_shadow_lux_drop",
            "diffuse_lux_threshold",
            "night_lux_threshold",
            "cold_lux_enter_threshold",
            "cool_air_delta",
            "storm_precipitation_trend_threshold",
            "storm_wind_trend_threshold",
            "storm_pressure_drop_threshold",
            "apply_cooldown_seconds",
            "position_tolerance",
            "observation_freshness_seconds",
        ):
            _number(getattr(self, name), name=name, minimum=0, maximum=100_000)
        _number(
            self.cold_lux_exit_threshold, name="cold_lux_exit_threshold", minimum=0, maximum=125_000
        )
        if self.cold_lux_exit_threshold <= self.cold_lux_enter_threshold:
            raise ValueError("cold_lux_exit_threshold must exceed cold_lux_enter_threshold")
        _number(
            self.environment_hysteresis_ratio,
            name="environment_hysteresis_ratio",
            minimum=0.01,
            maximum=0.99,
        )
        for name in ("environment_enter_seconds", "environment_exit_seconds"):
            _number(getattr(self, name), name=name, minimum=0.1, maximum=3600)
        if self.environment_exit_seconds < self.environment_enter_seconds:
            raise ValueError("environment_exit_seconds must be at least environment_enter_seconds")
        _number(
            self.movement_recovery_seconds,
            name="movement_recovery_seconds",
            minimum=self.position_settle_seconds,
            maximum=3600,
        )
        _number(
            self.heat_confidence_threshold,
            name="heat_confidence_threshold",
            minimum=0,
            maximum=1,
        )
        _number(
            self.glare_confidence_threshold,
            name="glare_confidence_threshold",
            minimum=0,
            maximum=1,
        )
        _number(
            self.minimum_incidence_factor, name="minimum_incidence_factor", minimum=0.001, maximum=1
        )
        _number(self.model_lux_per_watt, name="model_lux_per_watt", minimum=0.1, maximum=10000)
        _number(self.model_lux_ratio, name="model_lux_ratio", minimum=0, maximum=1)
        _number(
            self.position_settle_seconds, name="position_settle_seconds", minimum=0.1, maximum=3600
        )
        _number(
            self.movement_timeout_seconds,
            name="movement_timeout_seconds",
            minimum=self.position_settle_seconds,
            maximum=3600,
        )
        _number(self.cloud_cover_threshold, name="cloud_cover_threshold", minimum=0, maximum=100)
        if not 1 <= self.storm_required_signals <= 5:
            raise ValueError("storm_required_signals must be between 1 and 5")
        if self.opening_safety_polarity not in OPENING_SAFETY_POLARITIES:
            raise ValueError("opening_safety_polarity is not supported")
        if self.runtime_mode not in RUNTIME_MODES:
            raise ValueError("runtime_mode is not supported")
        if self.apply_owner not in APPLY_OWNERS:
            raise ValueError("apply_owner is not supported")
        allowed = set(INPUT_BINDING_KEYS) | set(LEGACY_BINDING_KEYS)
        for key, intent in self.binding_intents:
            if key not in allowed or intent not in BINDING_INTENTS:
                raise ValueError("binding_intents contains an invalid field intent")
        for key, policy in self.binding_freshness:
            if key not in allowed or not isinstance(policy, BindingFreshness):
                raise ValueError("binding_freshness contains an invalid field policy")

    @classmethod
    def defaults(cls) -> BlindControlConfig:
        return cls()

    def profile(self, name: str) -> PositionProfile:
        for profile_name, profile in self.profiles:
            if profile_name == name:
                return profile
        raise KeyError(name)

    def target(self, profile_name: str) -> float:
        return self.profile(profile_name).logical

    def device_position(self, logical: float) -> float:
        """Involutive transform, also used for observed device positions."""
        return 100 - logical if self.axis_inverted else logical

    def binding_policy(self, key: str, *, legacy: bool = False) -> BindingFreshness:
        """Resolve one policy while preserving the field's minimum age floor."""

        configured = dict(self.binding_freshness).get(key)
        policy = configured or default_binding_freshness(
            key,
            self.observation_freshness_seconds,
            legacy=legacy,
        )
        if legacy:
            return policy
        return BindingFreshness(
            _effective_max_age(key, policy.max_age_seconds),
            policy.require_timestamp,
            policy.owner,
        )

    def binding_freshness_mapping(self) -> dict[str, dict[str, object]]:
        """Expose effective owner/freshness policies for diagnostics and UX."""

        return {
            key: self.binding_policy(key, legacy=key in LEGACY_BINDING_KEYS).as_dict()
            for key in (*INPUT_BINDING_KEYS, *LEGACY_BINDING_KEYS)
        }

    def freshness_timer_seconds(self) -> float:
        """Return a bounded cadence that observes the shortest age-limited field."""

        configured_keys = set(dict(self.input_bindings)) | set(dict(self.legacy_bindings))
        if not configured_keys:
            return max(0.1, min(300.0, self.observation_freshness_seconds / 2))
        max_ages = [
            policy.max_age_seconds
            for key in (*INPUT_BINDING_KEYS, *LEGACY_BINDING_KEYS)
            if key in configured_keys
            if (
                policy := self.binding_policy(key, legacy=key in LEGACY_BINDING_KEYS)
            ).max_age_seconds
            is not None
        ]
        shortest = min(max_ages, default=self.observation_freshness_seconds)
        return max(0.1, min(300.0, shortest / 2))

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object] | None) -> BlindControlConfig:
        """Load persisted config without accepting unsafe or unknown profiles."""

        raw = raw or {}
        if int(raw.get("config_version", 5)) > CONFIG_VERSION:
            raise ValueError("unsupported future config version")
        observation_freshness_seconds = _number(
            raw.get("observation_freshness_seconds", 120),
            name="observation_freshness_seconds",
            minimum=1,
            maximum=86_400,
        )
        profiles = raw.get("profiles")
        cold_enter = float(raw.get("cold_lux_enter_threshold", raw.get("cold_lux_threshold", 400)))
        return cls(
            profiles=_profile_items(profiles),
            legacy_profile_values=_legacy_profile_values(raw),
            window_azimuth=_number(
                raw.get("window_azimuth", 124),
                name="window_azimuth",
                minimum=0,
                maximum=360,
            ),
            window_tilt=_number(
                raw.get("window_tilt", 90),
                name="window_tilt",
                minimum=0,
                maximum=180,
            ),
            axis_inverted=_bool(raw.get("axis_inverted", False), "axis_inverted"),
            automation_enabled=_bool(raw.get("automation_enabled", True), "automation_enabled"),
            apply_enabled=_bool(raw.get("apply_enabled", True), "apply_enabled"),
            runtime_mode=str(raw.get("runtime_mode", "shadow")),
            apply_owner=str(raw.get("apply_owner", "legacy")),
            core_contract_profile=str(raw.get("core_contract_profile", "benni")),
            core_contracts=tuple(sorted(dict(raw.get("core_contracts", {})).items())),
            open_meteo_api_url=(
                normalize_open_meteo_url(raw["open_meteo_api_url"])
                if raw.get("open_meteo_api_url")
                else ""
            ),
            opening_safety_polarity=str(raw.get("opening_safety_polarity", "unspecified")),
            input_bindings=_bindings(
                raw.get("input_bindings", raw.get("bindings")),
                name="input_bindings",
                allowed=INPUT_BINDING_KEYS,
            ),
            legacy_bindings=_bindings(
                raw.get("legacy_bindings"),
                name="legacy_bindings",
                allowed=LEGACY_BINDING_KEYS,
            ),
            binding_intents=_binding_intents(raw.get("binding_intents")),
            observation_freshness_seconds=observation_freshness_seconds,
            binding_freshness=_binding_freshness(
                raw.get("binding_freshness"), observation_freshness_seconds
            ),
            heat_outdoor_threshold=float(raw.get("heat_outdoor_threshold", 30)),
            heat_indoor_threshold=float(raw.get("heat_indoor_threshold", 26)),
            heat_radiation_threshold=float(raw.get("heat_radiation_threshold", 250)),
            heat_confidence_threshold=float(raw.get("heat_confidence_threshold", 0.55)),
            glare_confidence_threshold=float(raw.get("glare_confidence_threshold", 0.35)),
            cloud_shadow_lux_drop=float(raw.get("cloud_shadow_lux_drop", 1000)),
            cloud_cover_threshold=float(
                raw.get("cloud_cover_threshold", float(raw.get("cloud_shadow_ratio", 0.75)) * 100)
            ),
            model_lux_ratio=float(raw.get("model_lux_ratio", raw.get("cloud_shadow_ratio", 0.75))),
            minimum_incidence_factor=float(raw.get("minimum_incidence_factor", 0.05)),
            model_lux_per_watt=float(raw.get("model_lux_per_watt", 120)),
            diffuse_lux_threshold=float(raw.get("diffuse_lux_threshold", 2500)),
            night_lux_threshold=float(raw.get("night_lux_threshold", 50)),
            cold_outdoor_threshold=float(raw.get("cold_outdoor_threshold", 8)),
            cold_lux_enter_threshold=cold_enter,
            cold_lux_exit_threshold=float(
                raw.get("cold_lux_exit_threshold", max(cold_enter + 100, cold_enter * 1.25))
            ),
            environment_hysteresis_ratio=float(raw.get("environment_hysteresis_ratio", 0.8)),
            environment_enter_seconds=float(raw.get("environment_enter_seconds", 10)),
            environment_exit_seconds=float(raw.get("environment_exit_seconds", 120)),
            position_settle_seconds=float(raw.get("position_settle_seconds", 2)),
            movement_timeout_seconds=float(raw.get("movement_timeout_seconds", 120)),
            movement_recovery_seconds=float(
                raw.get(
                    "movement_recovery_seconds",
                    max(30, float(raw.get("position_settle_seconds", 2))),
                )
            ),
            cool_air_delta=float(raw.get("cool_air_delta", 2)),
            storm_precipitation_trend_threshold=float(
                raw.get("storm_precipitation_trend_threshold", 0)
            ),
            storm_wind_trend_threshold=float(raw.get("storm_wind_trend_threshold", 0)),
            storm_pressure_drop_threshold=float(raw.get("storm_pressure_drop_threshold", 0)),
            storm_required_signals=int(raw.get("storm_required_signals", 2)),
            apply_cooldown_seconds=float(raw.get("apply_cooldown_seconds", 60)),
            position_tolerance=float(raw.get("position_tolerance", 3)),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "config_version": CONFIG_VERSION,
            "profiles": {name: profile.as_dict() for name, profile in self.profiles},
            "legacy_profile_values": {
                name: {"normal": normal, "inverted": inverted}
                for name, normal, inverted in self.legacy_profile_values
            },
            "window_azimuth": self.window_azimuth,
            "window_tilt": self.window_tilt,
            "axis_inverted": self.axis_inverted,
            "automation_enabled": self.automation_enabled,
            "apply_enabled": self.apply_enabled,
            "runtime_mode": self.runtime_mode,
            "apply_owner": self.apply_owner,
            "core_contract_profile": self.core_contract_profile,
            "core_contracts": dict(self.core_contracts),
            "open_meteo_api_url": self.open_meteo_api_url,
            "opening_safety_polarity": self.opening_safety_polarity,
            "input_bindings": dict(self.input_bindings),
            "legacy_bindings": dict(self.legacy_bindings),
            "binding_intents": dict(self.binding_intents),
            "observation_freshness_seconds": self.observation_freshness_seconds,
            "binding_freshness": self.binding_freshness_mapping(),
            "heat_outdoor_threshold": self.heat_outdoor_threshold,
            "heat_indoor_threshold": self.heat_indoor_threshold,
            "heat_radiation_threshold": self.heat_radiation_threshold,
            "heat_confidence_threshold": self.heat_confidence_threshold,
            "glare_confidence_threshold": self.glare_confidence_threshold,
            "cloud_shadow_lux_drop": self.cloud_shadow_lux_drop,
            "cloud_cover_threshold": self.cloud_cover_threshold,
            "model_lux_ratio": self.model_lux_ratio,
            "minimum_incidence_factor": self.minimum_incidence_factor,
            "model_lux_per_watt": self.model_lux_per_watt,
            "diffuse_lux_threshold": self.diffuse_lux_threshold,
            "night_lux_threshold": self.night_lux_threshold,
            "cold_outdoor_threshold": self.cold_outdoor_threshold,
            "cold_lux_enter_threshold": self.cold_lux_enter_threshold,
            "cold_lux_exit_threshold": self.cold_lux_exit_threshold,
            "environment_hysteresis_ratio": self.environment_hysteresis_ratio,
            "environment_enter_seconds": self.environment_enter_seconds,
            "environment_exit_seconds": self.environment_exit_seconds,
            "position_settle_seconds": self.position_settle_seconds,
            "movement_timeout_seconds": self.movement_timeout_seconds,
            "movement_recovery_seconds": self.movement_recovery_seconds,
            "cool_air_delta": self.cool_air_delta,
            "storm_precipitation_trend_threshold": self.storm_precipitation_trend_threshold,
            "storm_wind_trend_threshold": self.storm_wind_trend_threshold,
            "storm_pressure_drop_threshold": self.storm_pressure_drop_threshold,
            "storm_required_signals": self.storm_required_signals,
            "apply_cooldown_seconds": self.apply_cooldown_seconds,
            "position_tolerance": self.position_tolerance,
        }


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def binding_requirement(key: str, *, legacy: bool = False) -> str:
    """Describe whether one selector is required, conditional, or optional."""

    if legacy:
        return "optional"
    if key in MANDATORY_AUTOMATIC_BINDING_KEYS | MANDATORY_TECHNICAL_BINDING_KEYS:
        return "required"
    if key in CONDITIONAL_BINDING_KEYS:
        return "conditional"
    return "optional"


def binding_status(config: BlindControlConfig, key: str, *, legacy: bool = False) -> str:
    """Return the installability state without exposing the selected entity ID."""

    bindings = dict(config.legacy_bindings if legacy else config.input_bindings)
    configured = key in bindings
    if legacy:
        return "legacy_bound" if configured else "legacy_not_available"
    if key in MANDATORY_AUTOMATIC_BINDING_KEYS | MANDATORY_TECHNICAL_BINDING_KEYS:
        return "required_resolved" if configured else "required_unresolved"
    if key in CONDITIONAL_BINDING_KEYS:
        if not configured:
            return "conditional_not_applicable"
        if config.opening_safety_polarity == "unspecified":
            return "conditional_unresolved"
        return "conditional_resolved"
    if key in {"expected_direct_radiation", "expected_diffuse_radiation"}:
        if configured:
            return "external_override_active"
        if config.open_meteo_api_url:
            return "internal_provider_active"
        return "provider_unavailable"
    return "optional_bound" if configured else "optional_intentionally_empty"


def _legacy_profile_values(raw: Mapping[str, object]) -> tuple[tuple[str, float, float], ...]:
    """Keep old explicit calibration for deliberate release rollback, never apply it."""
    values = raw.get("legacy_profile_values", {})
    if "legacy_profile_values" not in raw and int(raw.get("config_version", 5)) < 6:
        values = raw.get("profiles", {})
    if not isinstance(values, Mapping):
        raise ValueError("legacy profile values must be a mapping")
    result = []
    for name, item in values.items():
        if name not in DEFAULT_PROFILE_NAMES or not isinstance(item, Mapping):
            raise ValueError("invalid legacy profile")
        if "normal" in item and "inverted" in item:
            normal = _number(item["normal"], name="legacy normal", minimum=0, maximum=100)
            inverted = _number(item["inverted"], name="legacy inverted", minimum=0, maximum=100)
            result.append((name, normal, inverted))
    return tuple(result)
