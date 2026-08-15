"""Versioned, Home Assistant independent contracts for Blind Control.

The contracts deliberately contain observations with provenance and quality.  A
missing observation is not converted into a normal open state by this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import StrEnum


class InputQuality(StrEnum):
    """Quality states shared by all consumed observations."""

    FRESH = "fresh"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class OpeningState(StrEnum):
    """Opening values understood by the technical safety boundary."""

    CLOSED = "closed"
    OPEN = "open"
    TILTED = "tilted"
    UNKNOWN = "unknown"


class SolarExposureState(StrEnum):
    """Window-specific solar exposure states."""

    DIRECT_SUN = "direct_sun"
    CLOUD_SHADOW = "cloud_shadow"
    DIFFUSE_BRIGHT = "diffuse_bright"
    SOLAR_NOT_ON_WINDOW = "solar_not_on_window"
    NIGHT = "night"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class InputObservation[T]:
    """One owner-bound input value with freshness and provenance."""

    value: T | None = None
    source: str = "unbound"
    quality: InputQuality = InputQuality.UNKNOWN
    reason: str = "missing"
    updated_at: datetime | None = None

    @property
    def usable(self) -> bool:
        """Return whether the value is fresh enough for a positive decision."""

        return self.value is not None and self.quality is InputQuality.FRESH

    @classmethod
    def missing(cls, source: str = "unbound", reason: str = "missing") -> InputObservation[T]:
        """Create an explicitly unknown observation."""

        return cls(source=source, reason=reason)

    def as_dict(self) -> dict[str, object]:
        """Return a safe, JSON-compatible diagnostic projection."""

        return {
            "value": self.value,
            "source": self.source,
            "quality": self.quality.value,
            "reason": self.reason,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _missing[T]() -> InputObservation[T]:
    return InputObservation.missing()


@dataclass(frozen=True, slots=True)
class BlindControlInputs:
    """Consumed Core-State, technical and environment observations.

    The fields are intentionally generic contract values rather than Home
    Assistant entity IDs.  Binding an owner/source is a later integration
    boundary and cannot silently invent a production topology.
    """

    bio_state: InputObservation[str] = field(default_factory=_missing)
    activity_state: InputObservation[str] = field(default_factory=_missing)
    day_state: InputObservation[str] = field(default_factory=_missing)
    day_context: InputObservation[str] = field(default_factory=_missing)
    away: InputObservation[bool] = field(default_factory=_missing)
    private_time: InputObservation[bool] = field(default_factory=_missing)
    privacy: InputObservation[bool] = field(default_factory=_missing)

    opening_state: InputObservation[str] = field(default_factory=_missing)
    opening_safe_for_blind: InputObservation[bool] = field(default_factory=_missing)
    cover_available: InputObservation[bool] = field(default_factory=_missing)
    cover_ready: InputObservation[bool] = field(default_factory=_missing)
    cover_position: InputObservation[float] = field(default_factory=_missing)

    outdoor_lux: InputObservation[float] = field(default_factory=_missing)
    lux_trend: InputObservation[float] = field(default_factory=_missing)
    sun_elevation: InputObservation[float] = field(default_factory=_missing)
    sun_azimuth: InputObservation[float] = field(default_factory=_missing)
    expected_direct_radiation: InputObservation[float] = field(default_factory=_missing)
    expected_diffuse_radiation: InputObservation[float] = field(default_factory=_missing)
    cloud_cover: InputObservation[float] = field(default_factory=_missing)

    indoor_temperature: InputObservation[float] = field(default_factory=_missing)
    outdoor_temperature: InputObservation[float] = field(default_factory=_missing)
    indoor_temperature_trend: InputObservation[float] = field(default_factory=_missing)
    outdoor_temperature_trend: InputObservation[float] = field(default_factory=_missing)

    weather_alert: InputObservation[bool] = field(default_factory=_missing)
    precipitation_trend: InputObservation[float] = field(default_factory=_missing)
    wind_trend: InputObservation[float] = field(default_factory=_missing)
    pressure_trend: InputObservation[float] = field(default_factory=_missing)
    air_movement: InputObservation[bool] = field(default_factory=_missing)

    @classmethod
    def empty(cls) -> BlindControlInputs:
        """Return the safe unbound input set used by a newly installed entry."""

        return cls()

    def as_dict(self) -> dict[str, object]:
        """Return all input fields for a redaction-free, topology-free snapshot."""

        return {item.name: getattr(self, item.name).as_dict() for item in fields(self)}


@dataclass(frozen=True, slots=True)
class LegacyEvidence:
    """Owner-bound old-policy observations used for fieldwise Shadow parity."""

    observations: tuple[tuple[str, InputObservation[object]], ...] = ()
    configured: bool = False

    @classmethod
    def empty(cls) -> LegacyEvidence:
        return cls()

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> LegacyEvidence:
        """Keep the pure helper backwards compatible for explicit test evidence."""

        return cls(
            observations=tuple(
                (
                    key,
                    InputObservation(
                        value=value,
                        source="legacy_mapping",
                        quality=InputQuality.FRESH,
                        reason="explicit_legacy_mapping",
                    ),
                )
                for key, value in values.items()
            ),
            configured=True,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "configured": self.configured,
            "fields": {key: observation.as_dict() for key, observation in self.observations},
        }

    def as_mapping(self) -> dict[str, InputObservation[object]]:
        return dict(self.observations)


@dataclass(frozen=True, slots=True)
class ManualOverride:
    """A proven foreign cover intervention, never inferred from startup noise."""

    active: bool = False
    baseline: float | None = None
    observed_position: float | None = None
    source: str = "none"
    reason: str = "inactive"
    started_at: datetime | None = None

    @classmethod
    def inactive(cls, reason: str = "inactive") -> ManualOverride:
        return cls(reason=reason)

    def as_dict(self) -> dict[str, object]:
        return {
            "active": self.active,
            "baseline": self.baseline,
            "observed_position": self.observed_position,
            "source": self.source,
            "reason": self.reason,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


@dataclass(frozen=True, slots=True)
class Candidate:
    """One visible fachlicher requirement in the decision trace."""

    key: str
    category: str
    active: bool
    target_position: float | None
    source: str
    reason: str
    quality: InputQuality
    paused: bool = False
    suppressed_by: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "active": self.active,
            "target_position": self.target_position,
            "source": self.source,
            "reason": self.reason,
            "quality": self.quality.value,
            "paused": self.paused,
            "suppressed_by": self.suppressed_by,
        }


@dataclass(frozen=True, slots=True)
class PausedRequirement:
    """An environment branch explicitly paused by an exclusive mode."""

    key: str
    reason: str
    source: str

    def as_dict(self) -> dict[str, str]:
        return {"key": self.key, "reason": self.reason, "source": self.source}


@dataclass(frozen=True, slots=True)
class SolarExposure:
    """Window-specific solar fusion and its diagnostic evidence."""

    state: SolarExposureState
    confidence: float
    incidence_factor: float | None
    expected_radiation_w_m2: float | None
    observed_lux: float | None
    lux_trend: float | None
    cloud_shadow: bool
    sources: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "confidence": self.confidence,
            "incidence_factor": self.incidence_factor,
            "expected_radiation_w_m2": self.expected_radiation_w_m2,
            "observed_lux": self.observed_lux,
            "lux_trend": self.lux_trend,
            "cloud_shadow": self.cloud_shadow,
            "sources": list(self.sources),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Technical safety result kept separate from the fachlicher target."""

    status: str
    reason: str
    approved_target: float | None
    opening_state: str
    source: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "approved_target": self.approved_target,
            "opening_state": self.opening_state,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class ApplyDecision:
    """Shadow-only apply intent; it deliberately has no executable callback."""

    status: str
    reason: str
    requested_target: float | None
    approved_target: float | None
    cooldown_pending_target: float | None
    executed: bool = False
    write_path_reachable: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "requested_target": self.requested_target,
            "approved_target": self.approved_target,
            "cooldown_pending_target": self.cooldown_pending_target,
            "executed": self.executed,
            "write_path_reachable": self.write_path_reachable,
        }


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Complete machine-readable decision evidence for one evaluation."""

    version: str
    candidates: tuple[Candidate, ...]
    paused_requirements: tuple[PausedRequirement, ...]
    winner_keys: tuple[str, ...]
    fachlicher_target: float | None
    effective_target: float | None
    active_mode: str
    solar: SolarExposure
    safety: SafetyDecision
    apply: ApplyDecision
    override: ManualOverride
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "paused_requirements": [item.as_dict() for item in self.paused_requirements],
            "winner_keys": list(self.winner_keys),
            "fachlicher_target": self.fachlicher_target,
            "effective_target": self.effective_target,
            "active_mode": self.active_mode,
            "solar": self.solar.as_dict(),
            "safety": self.safety.as_dict(),
            "apply": self.apply.as_dict(),
            "override": self.override.as_dict(),
            "reasons": list(self.reasons),
        }
