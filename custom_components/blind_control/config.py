"""Validated, serializable Blind Control configuration defaults."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

CONFIG_VERSION = 1

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
}
_ENTITY_ID = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")


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
    return BindingFreshness(freshness_seconds, True, owner)


@dataclass(frozen=True, slots=True)
class PositionProfile:
    """Explicit normal and inverted-axis target positions."""

    normal: float
    inverted: float

    def __post_init__(self) -> None:
        for value in (self.normal, self.inverted):
            if not 0 <= value <= 100:
                raise ValueError("position values must be between 0 and 100")

    def target(self, axis_inverted: bool) -> float:
        return self.inverted if axis_inverted else self.normal

    def as_dict(self) -> dict[str, float]:
        return {"normal": self.normal, "inverted": self.inverted}


DEFAULT_PROFILES: tuple[tuple[str, PositionProfile], ...] = (
    ("window_safety", PositionProfile(100, 0)),
    ("privacy_bed", PositionProfile(40, 60)),
    ("waking", PositionProfile(100, 0)),
    ("sleep", PositionProfile(5, 60)),
    ("away", PositionProfile(5, 60)),
    ("private_time", PositionProfile(40, 60)),
    ("privacy", PositionProfile(40, 60)),
    ("heat_protection", PositionProfile(15, 55)),
    ("glare_general", PositionProfile(60, 40)),
    ("glare_tv", PositionProfile(60, 40)),
    ("glare_pc", PositionProfile(75, 25)),
    ("cold_insulation", PositionProfile(5, 60)),
    ("storm_approaching", PositionProfile(100, 0)),
    ("cool_air_available", PositionProfile(100, 0)),
    ("open", PositionProfile(100, 0)),
    ("manual_override", PositionProfile(50, 50)),
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
        defaults[name] = PositionProfile(
            _position(raw.get("normal")),
            _position(raw.get("inverted")),
        )
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
    window_azimuth: float = 124.0
    window_tilt: float = 90.0
    axis_inverted: bool = False
    automation_enabled: bool = True
    apply_enabled: bool = True
    input_bindings: tuple[tuple[str, str], ...] = ()
    legacy_bindings: tuple[tuple[str, str], ...] = ()
    observation_freshness_seconds: float = 120.0
    binding_freshness: tuple[tuple[str, BindingFreshness], ...] = ()

    heat_outdoor_threshold: float = 30.0
    heat_indoor_threshold: float = 26.0
    heat_radiation_threshold: float = 250.0
    heat_confidence_threshold: float = 0.55
    glare_confidence_threshold: float = 0.35
    cloud_shadow_lux_drop: float = 1000.0
    cloud_shadow_ratio: float = 0.75
    diffuse_lux_threshold: float = 2500.0
    night_lux_threshold: float = 50.0
    cold_outdoor_threshold: float = 8.0
    cool_air_delta: float = 2.0
    storm_precipitation_trend_threshold: float = 0.0
    storm_wind_trend_threshold: float = 0.0
    storm_pressure_drop_threshold: float = 0.0
    storm_required_signals: int = 2
    apply_cooldown_seconds: float = 60.0
    position_tolerance: float = 3.0

    def __post_init__(self) -> None:
        _number(self.window_azimuth, name="window_azimuth", minimum=0, maximum=360)
        _number(self.window_tilt, name="window_tilt", minimum=0, maximum=180)
        for name in (
            "heat_outdoor_threshold",
            "heat_indoor_threshold",
            "heat_radiation_threshold",
            "cloud_shadow_lux_drop",
            "diffuse_lux_threshold",
            "night_lux_threshold",
            "cold_outdoor_threshold",
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
        _number(self.cloud_shadow_ratio, name="cloud_shadow_ratio", minimum=0, maximum=1)
        if not 1 <= self.storm_required_signals <= 5:
            raise ValueError("storm_required_signals must be between 1 and 5")
        allowed = set(INPUT_BINDING_KEYS) | set(LEGACY_BINDING_KEYS)
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
        return self.profile(profile_name).target(self.axis_inverted)

    def binding_policy(self, key: str, *, legacy: bool = False) -> BindingFreshness:
        """Resolve one explicit policy without applying a global age heuristic."""

        configured = dict(self.binding_freshness).get(key)
        return configured or default_binding_freshness(
            key,
            self.observation_freshness_seconds,
            legacy=legacy,
        )

    def binding_freshness_mapping(self) -> dict[str, dict[str, object]]:
        """Expose effective owner/freshness policies for diagnostics and UX."""

        return {
            key: self.binding_policy(key, legacy=key in LEGACY_BINDING_KEYS).as_dict()
            for key in (*INPUT_BINDING_KEYS, *LEGACY_BINDING_KEYS)
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object] | None) -> BlindControlConfig:
        """Load persisted config without accepting unsafe or unknown profiles."""

        raw = raw or {}
        observation_freshness_seconds = _number(
            raw.get("observation_freshness_seconds", 120),
            name="observation_freshness_seconds",
            minimum=1,
            maximum=86_400,
        )
        profiles = raw.get("profiles")
        return cls(
            profiles=_profile_items(profiles),
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
            cloud_shadow_ratio=float(raw.get("cloud_shadow_ratio", 0.75)),
            diffuse_lux_threshold=float(raw.get("diffuse_lux_threshold", 2500)),
            night_lux_threshold=float(raw.get("night_lux_threshold", 50)),
            cold_outdoor_threshold=float(raw.get("cold_outdoor_threshold", 8)),
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
            "window_azimuth": self.window_azimuth,
            "window_tilt": self.window_tilt,
            "axis_inverted": self.axis_inverted,
            "automation_enabled": self.automation_enabled,
            "apply_enabled": self.apply_enabled,
            "input_bindings": dict(self.input_bindings),
            "legacy_bindings": dict(self.legacy_bindings),
            "observation_freshness_seconds": self.observation_freshness_seconds,
            "binding_freshness": self.binding_freshness_mapping(),
            "heat_outdoor_threshold": self.heat_outdoor_threshold,
            "heat_indoor_threshold": self.heat_indoor_threshold,
            "heat_radiation_threshold": self.heat_radiation_threshold,
            "heat_confidence_threshold": self.heat_confidence_threshold,
            "glare_confidence_threshold": self.glare_confidence_threshold,
            "cloud_shadow_lux_drop": self.cloud_shadow_lux_drop,
            "cloud_shadow_ratio": self.cloud_shadow_ratio,
            "diffuse_lux_threshold": self.diffuse_lux_threshold,
            "night_lux_threshold": self.night_lux_threshold,
            "cold_outdoor_threshold": self.cold_outdoor_threshold,
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
