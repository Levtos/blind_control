"""Read-only Home Assistant coordinator for current Open-Meteo radiation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .open_meteo import (
    OPEN_METEO_FRESHNESS_SECONDS,
    OPEN_METEO_UPDATE_INTERVAL_SECONDS,
    OpenMeteoPayloadError,
    OpenMeteoRadiationData,
    parse_open_meteo_payload,
)

_LOGGER = logging.getLogger(__name__)


class OpenMeteoRadiationCoordinator(DataUpdateCoordinator[OpenMeteoRadiationData]):
    """Fetch both radiation values in one request and expose no command path."""

    def __init__(self, hass, entry, api_url: str | None) -> None:
        self._api_url = api_url
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Blind Control Open-Meteo radiation",
            update_interval=(
                timedelta(seconds=OPEN_METEO_UPDATE_INTERVAL_SECONDS) if api_url else None
            ),
            always_update=True,
        )

    @property
    def configured(self) -> bool:
        """Return whether a validated provider URL exists without exposing it."""

        return self._api_url is not None

    def provider_status(self, *, now: datetime | None = None) -> str:
        """Classify provider health independently from the stored value."""

        if not self.configured:
            return "unconfigured"
        if self.data is None:
            return "unavailable"
        now = now or datetime.now(UTC)
        if (now - self.data.fetched_at).total_seconds() > OPEN_METEO_FRESHNESS_SECONDS:
            return "stale"
        return "ready" if self.last_update_success else "degraded"

    async def _async_update_data(self) -> OpenMeteoRadiationData:
        if self._api_url is None:
            raise UpdateFailed("provider_not_configured")
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                self._api_url,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                payload = await response.json()
            return parse_open_meteo_payload(payload, fetched_at=datetime.now(UTC))
        except OpenMeteoPayloadError:
            raise UpdateFailed("provider_payload_invalid") from None
        except (TimeoutError, aiohttp.ClientError, ValueError):
            raise UpdateFailed("provider_request_failed") from None
