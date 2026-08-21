"""Pure Open-Meteo radiation URL and payload contracts.

The module deliberately has no Home Assistant dependency.  It keeps the
provider replaceable and prevents request URLs or coordinates from entering
the public decision and diagnostics contracts.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

OPEN_METEO_HOST = "api.open-meteo.com"
OPEN_METEO_PATH = "/v1/forecast"
OPEN_METEO_MODEL = "dwd_icon_seamless"
OPEN_METEO_PROVIDER = "open_meteo"
OPEN_METEO_UPDATE_INTERVAL_SECONDS = 900
OPEN_METEO_FRESHNESS_SECONDS = 1200
DIRECT_RADIATION_FIELD = "direct_normal_irradiance_instant"
DIFFUSE_RADIATION_FIELD = "diffuse_radiation_instant"
RADIATION_FIELDS = (DIRECT_RADIATION_FIELD, DIFFUSE_RADIATION_FIELD)

_ALLOWED_QUERY_KEYS = frozenset({"latitude", "longitude", "current", "models", "timezone"})
_DATA_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?$")
_TIMEZONE = re.compile(r"^(?:auto|UTC|GMT|[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)+)$")


class OpenMeteoUrlError(ValueError):
    """Raised for a URL that violates the fixed provider contract."""


class OpenMeteoPayloadError(ValueError):
    """Raised for an incomplete or non-numeric provider payload."""


@dataclass(frozen=True, slots=True)
class OpenMeteoRadiationData:
    """Both radiation values obtained atomically from one response."""

    direct_normal_irradiance: float
    diffuse_radiation: float
    fetched_at: datetime
    data_timestamp: str | None


def suggested_open_meteo_url(
    latitude: float,
    longitude: float,
    timezone: str = "UTC",
) -> str:
    """Build the fixed current-radiation URL from Home Assistant location data."""

    return urlunsplit(
        (
            "https",
            OPEN_METEO_HOST,
            OPEN_METEO_PATH,
            urlencode(
                (
                    ("latitude", _coordinate(latitude, latitude=True)),
                    ("longitude", _coordinate(longitude, latitude=False)),
                    ("current", ",".join(RADIATION_FIELDS)),
                    ("models", OPEN_METEO_MODEL),
                    ("timezone", str(timezone or "UTC")),
                )
            ),
            "",
        )
    )


def normalize_open_meteo_url(value: object) -> str:
    """Validate and canonicalize a complete Open-Meteo forecast URL."""

    if not isinstance(value, str) or not value.strip():
        raise OpenMeteoUrlError("open_meteo_url_required")
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError:
        raise OpenMeteoUrlError("open_meteo_url_invalid") from None
    if parsed.scheme.lower() != "https":
        raise OpenMeteoUrlError("open_meteo_url_invalid_scheme")
    if parsed.username is not None or parsed.password is not None:
        raise OpenMeteoUrlError("open_meteo_url_userinfo_forbidden")
    if parsed.hostname != OPEN_METEO_HOST or port not in (None, 443):
        raise OpenMeteoUrlError("open_meteo_url_invalid_host")
    if parsed.path != OPEN_METEO_PATH or parsed.fragment:
        raise OpenMeteoUrlError("open_meteo_url_invalid_endpoint")

    pairs = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    if any(key not in _ALLOWED_QUERY_KEYS for key, _value in pairs):
        raise OpenMeteoUrlError("open_meteo_url_forbidden_parameter")
    if len({key for key, _value in pairs}) != len(pairs):
        raise OpenMeteoUrlError("open_meteo_url_duplicate_parameter")
    query = dict(pairs)
    if not {"latitude", "longitude", "current", "models"}.issubset(query):
        raise OpenMeteoUrlError("open_meteo_url_missing_parameter")
    latitude = _coordinate(query["latitude"], latitude=True)
    longitude = _coordinate(query["longitude"], latitude=False)
    if query["models"] != OPEN_METEO_MODEL:
        raise OpenMeteoUrlError("open_meteo_url_invalid_model")
    current = tuple(part.strip() for part in query["current"].split(",") if part.strip())
    if set(current) != set(RADIATION_FIELDS):
        raise OpenMeteoUrlError("open_meteo_url_invalid_current_fields")

    canonical = [
        ("latitude", latitude),
        ("longitude", longitude),
        ("current", ",".join(RADIATION_FIELDS)),
        ("models", OPEN_METEO_MODEL),
    ]
    if timezone := query.get("timezone"):
        if not _TIMEZONE.fullmatch(timezone):
            raise OpenMeteoUrlError("open_meteo_url_invalid_timezone")
        canonical.append(("timezone", timezone))
    return urlunsplit(("https", OPEN_METEO_HOST, OPEN_METEO_PATH, urlencode(canonical), ""))


def parse_open_meteo_payload(payload: object, *, fetched_at: datetime) -> OpenMeteoRadiationData:
    """Extract the two distinct current values without inventing defaults."""

    if not isinstance(payload, dict) or not isinstance(payload.get("current"), dict):
        raise OpenMeteoPayloadError("provider_payload_missing_current")
    current: dict[str, Any] = payload["current"]
    direct = _radiation(current.get(DIRECT_RADIATION_FIELD))
    diffuse = _radiation(current.get(DIFFUSE_RADIATION_FIELD))
    timestamp = current.get("time")
    safe_timestamp = (
        timestamp if isinstance(timestamp, str) and _DATA_TIMESTAMP.fullmatch(timestamp) else None
    )
    return OpenMeteoRadiationData(
        direct_normal_irradiance=direct,
        diffuse_radiation=diffuse,
        fetched_at=fetched_at,
        data_timestamp=safe_timestamp,
    )


def _coordinate(value: object, *, latitude: bool) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        raise OpenMeteoUrlError("open_meteo_url_invalid_coordinates") from None
    limit = 90 if latitude else 180
    if not math.isfinite(numeric) or not -limit <= numeric <= limit:
        raise OpenMeteoUrlError("open_meteo_url_invalid_coordinates")
    return format(numeric, ".6f").rstrip("0").rstrip(".")


def _radiation(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as err:
        raise OpenMeteoPayloadError("provider_payload_invalid_radiation") from err
    if not math.isfinite(numeric) or numeric < 0:
        raise OpenMeteoPayloadError("provider_payload_invalid_radiation")
    return numeric
