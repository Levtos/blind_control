"""Validated, serializable Blind Control configuration defaults."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

CONFIG_VERSION = 1


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


@dataclass(frozen=True, slots=True)
class BlindControlConfig:
    """All runtime-calibratable values for the deterministic shadow engine."""

    profiles: tuple[tuple[str, PositionProfile], ...] = DEFAULT_PROFILES
    window_azimuth: float = 124.0
    window_tilt: float = 90.0
    axis_inverted: bool = False
    automation_enabled: bool = True
    apply_enabled: bool = True

    heat_outdoor_threshold: float = 30.0
    heat_indoor_threshold: float = 26.0
    heat_radiation_threshold: float = 250.0
    heat_confidence_threshold: float = 0.55
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
        ):
            _number(getattr(self, name), name=name, minimum=0, maximum=100_000)
        _number(
            self.heat_confidence_threshold,
            name="heat_confidence_threshold",
            minimum=0,
            maximum=1,
        )
        _number(self.cloud_shadow_ratio, name="cloud_shadow_ratio", minimum=0, maximum=1)
        if not 1 <= self.storm_required_signals <= 5:
            raise ValueError("storm_required_signals must be between 1 and 5")

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

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object] | None) -> BlindControlConfig:
        """Load persisted config without accepting unsafe or unknown profiles."""

        raw = raw or {}
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
            heat_outdoor_threshold=float(raw.get("heat_outdoor_threshold", 30)),
            heat_indoor_threshold=float(raw.get("heat_indoor_threshold", 26)),
            heat_radiation_threshold=float(raw.get("heat_radiation_threshold", 250)),
            heat_confidence_threshold=float(raw.get("heat_confidence_threshold", 0.55)),
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
            "heat_outdoor_threshold": self.heat_outdoor_threshold,
            "heat_indoor_threshold": self.heat_indoor_threshold,
            "heat_radiation_threshold": self.heat_radiation_threshold,
            "heat_confidence_threshold": self.heat_confidence_threshold,
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
