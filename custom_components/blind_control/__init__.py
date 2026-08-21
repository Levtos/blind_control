"""Bootstrap runtime for the Blind Control Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .config import BlindControlConfig
from .coordinator import ShadowCoordinator
from .open_meteo import suggested_open_meteo_url
from .radiation_provider import OpenMeteoRadiationCoordinator
from .shadow import ShadowRuntime, ShadowSnapshot
from .websocket_api import register_websocket_commands

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR,)


@dataclass(slots=True)
class BlindControlRuntimeData:
    """Shadow state owned by one loaded Blind Control ConfigEntry."""

    phase: str = "shadow"
    config: BlindControlConfig = field(default_factory=BlindControlConfig.defaults)
    shadow: ShadowRuntime = field(default_factory=ShadowRuntime)
    snapshot: ShadowSnapshot | None = None
    ux_snapshot: dict[str, object] | None = None
    coordinator: ShadowCoordinator | None = None
    radiation_provider: OpenMeteoRadiationCoordinator | None = None


type BlindControlConfigEntry = ConfigEntry[BlindControlRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Prepare the read-only transport and install the Shadow sidebar panel."""

    register_websocket_commands(hass)
    from .panel import async_register_panel

    await async_register_panel(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Load one non-actuating entry and start its owner-bound observer."""

    config = BlindControlConfig.from_mapping(_runtime_config_mapping(hass, entry))
    radiation_provider = OpenMeteoRadiationCoordinator(
        hass,
        entry,
        config.open_meteo_api_url or None,
    )
    if radiation_provider.configured:
        await radiation_provider.async_refresh()
    shadow = ShadowRuntime(config)
    coordinator = ShadowCoordinator(
        hass,
        entry,
        config,
        shadow,
        radiation_provider=radiation_provider,
    )
    entry.runtime_data = BlindControlRuntimeData(
        config=config,
        shadow=shadow,
        coordinator=coordinator,
        radiation_provider=radiation_provider,
    )
    await coordinator.async_start()
    if hasattr(entry, "async_on_unload"):
        entry.async_on_unload(coordinator.stop)
    if hasattr(entry, "add_update_listener") and hasattr(entry, "async_on_unload"):
        entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _runtime_config_mapping(
    hass: HomeAssistant, entry: BlindControlConfigEntry
) -> dict[str, object]:
    """Use HA's location as a non-persistent provider prefill for legacy entries.

    Entries created before the internal provider existed have no URL yet.  The
    generated value stays in runtime memory until the user confirms it in the
    native ConfigFlow/OptionsFlow; no coordinate or URL is exposed by a public
    contract.
    """

    raw = {
        **getattr(entry, "data", {}),
        **getattr(entry, "options", {}),
    }
    if raw.get("open_meteo_api_url"):
        return raw
    home_config = getattr(hass, "config", None)
    latitude = getattr(home_config, "latitude", None)
    longitude = getattr(home_config, "longitude", None)
    if latitude is None or longitude is None:
        return raw
    try:
        raw["open_meteo_api_url"] = suggested_open_meteo_url(
            latitude,
            longitude,
            getattr(home_config, "time_zone", "UTC"),
        )
    except (TypeError, ValueError):
        return raw
    return raw


async def async_unload_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Unload one entry and remove only observation listeners."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False
    runtime_data = getattr(entry, "runtime_data", None)
    coordinator = getattr(runtime_data, "coordinator", None)
    if coordinator is not None:
        coordinator.stop()
    radiation_provider = getattr(runtime_data, "radiation_provider", None)
    if radiation_provider is not None:
        await radiation_provider.async_shutdown()
    return True


async def _async_options_updated(hass: HomeAssistant, entry: BlindControlConfigEntry) -> None:
    """Recreate the read-only snapshot after an OptionsFlow change."""

    await hass.config_entries.async_reload(entry.entry_id)
