"""Independent, documented solar-exposure calculation for the window surface."""

from __future__ import annotations

import math

from .config import BlindControlConfig
from .contracts import (
    BlindControlInputs,
    SolarExposure,
    SolarExposureState,
)


def calculate_solar_exposure(
    inputs: BlindControlInputs,
    config: BlindControlConfig,
) -> SolarExposure:
    """Fuse geometry, model radiation, local lux and cloud evidence.

    The function consumes sun/weather/lux observations; it does not create a
    second raw sun, weather or temperature owner.  The geometry is a standard
    vector dot product for a plane whose azimuth is measured clockwise from
    north and whose tilt is measured from horizontal.
    """

    sun_elevation = inputs.sun_elevation
    sun_azimuth = inputs.sun_azimuth
    lux = inputs.outdoor_lux
    lux_trend = inputs.lux_trend
    direct = inputs.expected_direct_radiation
    diffuse = inputs.expected_diffuse_radiation
    cloud_cover = inputs.cloud_cover

    sources = tuple(
        observation.source
        for observation in (sun_elevation, sun_azimuth, lux, direct, diffuse, cloud_cover)
        if observation.usable
    )

    if not sun_elevation.usable and not lux.usable:
        return _unknown(
            sources=sources,
            observed_lux=None,
            lux_trend=_number(lux_trend),
            reason="sun_and_lux_not_fresh",
        )

    if sun_elevation.usable and float(sun_elevation.value) <= 0:
        return SolarExposure(
            state=SolarExposureState.NIGHT,
            confidence=0.98,
            incidence_factor=0.0,
            expected_radiation_w_m2=0.0,
            observed_lux=_number(lux),
            lux_trend=_number(lux_trend),
            cloud_shadow=False,
            sources=sources,
            reason="sun_below_horizon",
        )

    if lux.usable and float(lux.value) <= config.night_lux_threshold:
        return SolarExposure(
            state=SolarExposureState.NIGHT,
            confidence=0.86 if sun_elevation.usable else 0.72,
            incidence_factor=0.0 if not sun_azimuth.usable else None,
            expected_radiation_w_m2=0.0,
            observed_lux=float(lux.value),
            lux_trend=_number(lux_trend),
            cloud_shadow=False,
            sources=sources,
            reason="local_lux_below_night_threshold",
        )

    if not sun_elevation.usable or not sun_azimuth.usable:
        return _unknown(
            sources=sources,
            observed_lux=_number(lux),
            lux_trend=_number(lux_trend),
            reason="sun_geometry_not_fresh",
        )

    incidence = _incidence_factor(
        sun_elevation=float(sun_elevation.value),
        sun_azimuth=float(sun_azimuth.value),
        window_azimuth=config.window_azimuth,
        window_tilt=config.window_tilt,
    )
    direct_radiation = max(0.0, _number(direct) or 0.0)
    diffuse_radiation = max(0.0, _number(diffuse) or 0.0)
    expected = direct_radiation * incidence + diffuse_radiation * 0.5
    lux_value = _number(lux)
    trend = _number(lux_trend)
    cloud_value = _number(cloud_cover)
    model_lux = expected * 120.0

    if incidence < 0.05:
        state = SolarExposureState.SOLAR_NOT_ON_WINDOW
        reason = "sun_geometry_does_not_hit_window"
        cloud_shadow = False
    elif _is_cloud_shadow(
        cloud_cover=cloud_value,
        lux=lux_value,
        lux_trend=trend,
        model_lux=model_lux,
        config=config,
        direct_radiation=direct_radiation,
    ):
        state = SolarExposureState.CLOUD_SHADOW
        reason = "direct_geometry_with_cloud_or_observed_lux_drop"
        cloud_shadow = True
    elif direct_radiation >= config.heat_radiation_threshold:
        state = SolarExposureState.DIRECT_SUN
        reason = "direct_geometry_and_relevant_radiation"
        cloud_shadow = False
    elif lux_value is not None and lux_value >= config.diffuse_lux_threshold:
        state = SolarExposureState.DIFFUSE_BRIGHT
        reason = "bright_local_lux_without_direct_radiation"
        cloud_shadow = False
    else:
        state = SolarExposureState.UNKNOWN
        reason = "insufficient_radiation_or_lux_evidence"
        cloud_shadow = False

    confidence = _confidence(
        lux=lux,
        direct=direct,
        diffuse=diffuse,
        cloud=cloud_cover,
        incidence=incidence,
    )
    return SolarExposure(
        state=state,
        confidence=confidence,
        incidence_factor=incidence,
        expected_radiation_w_m2=expected,
        observed_lux=lux_value,
        lux_trend=trend,
        cloud_shadow=cloud_shadow,
        sources=sources,
        reason=reason,
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
    return max(0.0, min(1.0, sum(a * b for a, b in zip(sun_vector, window_normal, strict=True))))


def _is_cloud_shadow(
    *,
    cloud_cover: float | None,
    lux: float | None,
    lux_trend: float | None,
    model_lux: float,
    config: BlindControlConfig,
    direct_radiation: float,
) -> bool:
    if direct_radiation < config.heat_radiation_threshold:
        return False
    if cloud_cover is not None and cloud_cover >= config.cloud_shadow_ratio:
        return True
    if lux_trend is not None and lux_trend <= -config.cloud_shadow_lux_drop:
        return True
    return (
        cloud_cover is None
        and model_lux > 0
        and lux is not None
        and lux < model_lux * config.cloud_shadow_ratio
    )


def _confidence(
    *,
    lux,
    direct,
    diffuse,
    cloud,
    incidence: float,
) -> float:
    quality_points = sum(observation.usable for observation in (lux, direct, diffuse, cloud))
    evidence = 0.35 + quality_points * 0.12
    return round(max(0.0, min(1.0, evidence * (0.55 + incidence * 0.45))), 3)


def _unknown(
    *,
    sources: tuple[str, ...],
    observed_lux: float | None,
    lux_trend: float | None,
    reason: str,
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
    )


def _number(observation) -> float | None:
    if not observation.usable:
        return None
    return float(observation.value)
