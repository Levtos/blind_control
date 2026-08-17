"""Capability-aware solar exposure for the configured window surface."""

from __future__ import annotations

import math

from .config import BlindControlConfig
from .contracts import (
    BlindControlInputs,
    InputObservation,
    QualityBlocker,
    SolarExposure,
    SolarExposureState,
)

_OPTIONAL_SOLAR_KEYS = (
    "lux_trend",
    "expected_direct_radiation",
    "expected_diffuse_radiation",
    "cloud_cover",
)
_SOLAR_KEYS = (
    "sun_elevation",
    "sun_azimuth",
    "outdoor_lux",
    *_OPTIONAL_SOLAR_KEYS,
)


def calculate_solar_exposure(
    inputs: BlindControlInputs,
    config: BlindControlConfig,
) -> SolarExposure:
    """Fuse mandatory geometry/lux with optional model and trend evidence."""

    observations = {key: getattr(inputs, key) for key in _SOLAR_KEYS}
    capabilities = tuple(
        key for key, observation in observations.items() if _has_capability(observation)
    )
    missing_optional = tuple(key for key in _OPTIONAL_SOLAR_KEYS if key not in capabilities)
    used = tuple(key for key, observation in observations.items() if observation.usable)
    derived = tuple(
        key
        for key, observation in observations.items()
        if observation.usable and observation.reason.startswith("derived_")
    )
    sources = tuple(
        dict.fromkeys(
            observation.source for observation in observations.values() if observation.usable
        )
    )

    elevation = inputs.sun_elevation
    azimuth = inputs.sun_azimuth
    lux = inputs.outdoor_lux
    trend = inputs.lux_trend
    direct = inputs.expected_direct_radiation
    diffuse = inputs.expected_diffuse_radiation
    cloud = inputs.cloud_cover

    if elevation.usable and float(elevation.value) <= 0:
        return SolarExposure(
            state=SolarExposureState.NIGHT,
            confidence=0.98,
            incidence_factor=0.0,
            expected_radiation_w_m2=0.0,
            observed_lux=_number(lux),
            lux_trend=_number(trend),
            cloud_shadow=False,
            sources=sources,
            reason="sun_below_horizon",
            capabilities=capabilities,
            missing_optional_capabilities=missing_optional,
            used_evidence=used,
            derived_evidence=derived,
        )

    if not elevation.usable and lux.usable and float(lux.value) <= config.night_lux_threshold:
        return SolarExposure(
            state=SolarExposureState.NIGHT,
            confidence=0.55,
            incidence_factor=None,
            expected_radiation_w_m2=0.0,
            observed_lux=float(lux.value),
            lux_trend=_number(trend),
            cloud_shadow=False,
            sources=sources,
            reason="local_lux_night_hint_without_sufficient_geometry",
            capabilities=capabilities,
            missing_optional_capabilities=missing_optional,
            used_evidence=used,
            derived_evidence=derived,
            quality_blockers=(_blocker("sun_elevation", elevation),),
        )

    blockers = tuple(
        _blocker(key, getattr(inputs, key))
        for key in ("sun_elevation", "sun_azimuth", "outdoor_lux")
        if not getattr(inputs, key).usable
    )
    if blockers:
        return _unknown(
            sources=sources,
            observed_lux=_number(lux),
            lux_trend=_number(trend),
            reason="insufficient_mandatory_solar_evidence",
            capabilities=capabilities,
            missing_optional=missing_optional,
            used=used,
            derived=derived,
            blockers=blockers,
        )

    incidence = _incidence_factor(
        sun_elevation=float(elevation.value),
        sun_azimuth=float(azimuth.value),
        window_azimuth=config.window_azimuth,
        window_tilt=config.window_tilt,
    )
    direct_value = _number(direct)
    diffuse_value = _number(diffuse)
    expected = None
    if direct_value is not None or diffuse_value is not None:
        expected = max(0.0, direct_value or 0.0) * incidence + max(0.0, diffuse_value or 0.0) * 0.5
    lux_value = float(lux.value)
    trend_value = _number(trend)
    cloud_value = _number(cloud)
    model_lux = expected * 120.0 if expected is not None else None

    if incidence < 0.05:
        state = SolarExposureState.SOLAR_NOT_ON_WINDOW
        reason = "sun_geometry_does_not_hit_window"
        cloud_shadow = False
    elif _is_cloud_shadow(
        cloud_cover=cloud_value,
        lux=lux_value,
        lux_trend=trend_value,
        model_lux=model_lux,
        config=config,
        direct_radiation=direct_value,
    ):
        state = SolarExposureState.CLOUD_SHADOW
        reason = "direct_geometry_with_cloud_or_observed_lux_drop"
        cloud_shadow = True
    elif direct_value is not None and direct_value >= config.heat_radiation_threshold:
        state = SolarExposureState.DIRECT_SUN
        reason = "direct_geometry_and_relevant_model_radiation"
        cloud_shadow = False
    elif lux_value >= config.diffuse_lux_threshold:
        state = SolarExposureState.DIFFUSE_BRIGHT
        reason = "geometry_and_bright_local_lux"
        cloud_shadow = False
    else:
        state = SolarExposureState.UNKNOWN
        reason = "insufficient_radiation_or_lux_evidence_with_known_geometry"
        cloud_shadow = False

    return SolarExposure(
        state=state,
        confidence=_confidence(inputs, incidence),
        incidence_factor=incidence,
        expected_radiation_w_m2=expected,
        observed_lux=lux_value,
        lux_trend=trend_value,
        cloud_shadow=cloud_shadow,
        sources=sources,
        reason=reason,
        capabilities=capabilities,
        missing_optional_capabilities=missing_optional,
        used_evidence=used,
        derived_evidence=derived,
    )


def _incidence_factor(
    *, sun_elevation: float, sun_azimuth: float, window_azimuth: float, window_tilt: float
) -> float:
    """Return the positive dot product between sun vector and window normal."""

    elevation = math.radians(sun_elevation)
    azimuth = math.radians(sun_azimuth % 360)
    tilt = math.radians(window_tilt)
    sun_vector = (
        math.cos(elevation) * math.sin(azimuth),
        math.cos(elevation) * math.cos(azimuth),
        math.sin(elevation),
    )
    window_normal = (
        math.sin(tilt) * math.sin(math.radians(window_azimuth % 360)),
        math.sin(tilt) * math.cos(math.radians(window_azimuth % 360)),
        math.cos(tilt),
    )
    return max(
        0.0,
        min(1.0, sum(a * b for a, b in zip(sun_vector, window_normal, strict=True))),
    )


def _is_cloud_shadow(
    *,
    cloud_cover: float | None,
    lux: float,
    lux_trend: float | None,
    model_lux: float | None,
    config: BlindControlConfig,
    direct_radiation: float | None,
) -> bool:
    if direct_radiation is not None and direct_radiation < config.heat_radiation_threshold:
        return False
    if cloud_cover is not None and cloud_cover >= config.cloud_shadow_ratio:
        return True
    if lux_trend is not None and lux_trend <= -config.cloud_shadow_lux_drop:
        return True
    return (
        direct_radiation is not None
        and cloud_cover is None
        and model_lux is not None
        and model_lux > 0
        and lux < model_lux * config.cloud_shadow_ratio
    )


def _confidence(inputs: BlindControlInputs, incidence: float) -> float:
    score = 0.0
    if inputs.sun_elevation.usable and inputs.sun_azimuth.usable:
        score += 0.35
    if inputs.outdoor_lux.usable:
        score += 0.25
    if inputs.lux_trend.usable:
        score += 0.08
    if inputs.expected_direct_radiation.usable:
        score += 0.12
    if inputs.expected_diffuse_radiation.usable:
        score += 0.1
    if inputs.cloud_cover.usable:
        score += 0.1
    if incidence < 0.05 and inputs.sun_elevation.usable and inputs.sun_azimuth.usable:
        score = max(score, 0.75)
    return round(min(1.0, score), 3)


def _unknown(
    *,
    sources: tuple[str, ...],
    observed_lux: float | None,
    lux_trend: float | None,
    reason: str,
    capabilities: tuple[str, ...],
    missing_optional: tuple[str, ...],
    used: tuple[str, ...],
    derived: tuple[str, ...],
    blockers: tuple[QualityBlocker, ...],
) -> SolarExposure:
    return SolarExposure(
        state=SolarExposureState.UNKNOWN,
        confidence=0.0,
        incidence_factor=None,
        expected_radiation_w_m2=None,
        observed_lux=observed_lux,
        lux_trend=lux_trend,
        cloud_shadow=False,
        sources=sources,
        reason=reason,
        capabilities=capabilities,
        missing_optional_capabilities=missing_optional,
        used_evidence=used,
        derived_evidence=derived,
        quality_blockers=blockers,
    )


def _number(observation: InputObservation[object]) -> float | None:
    if not observation.usable:
        return None
    return float(observation.value)


def _has_capability(observation: InputObservation[object]) -> bool:
    return observation.reason != "owner_binding_not_configured"


def _blocker(key: str, observation: InputObservation[object]) -> QualityBlocker:
    return QualityBlocker(key=key, quality=observation.quality, reason=observation.reason)
