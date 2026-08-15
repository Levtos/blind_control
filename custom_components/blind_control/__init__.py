"""Bootstrap runtime for the Blind Control Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .config import BlindControlConfig
from .coordinator import ShadowCoordinator
from .shadow import ShadowRuntime, ShadowSnapshot
from .websocket_api import register_websocket_commands


@dataclass(slots=True)
class BlindControlRuntimeData:
    """Shadow state owned by one loaded Blind Control ConfigEntry."""

    phase: str = "shadow"
    config: BlindControlConfig = field(default_factory=BlindControlConfig.defaults)
    shadow: ShadowRuntime = field(default_factory=ShadowRuntime)
    snapshot: ShadowSnapshot | None = None
    ux_snapshot: dict[str, object] | None = None
    coordinator: ShadowCoordinator | None = None


type BlindControlConfigEntry = ConfigEntry[BlindControlRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Prepare the read-only transport and install the Shadow sidebar panel."""

    register_websocket_commands(hass)
    from .panel import async_register_panel

    await async_register_panel(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Load one non-actuating entry and start its owner-bound observer."""

    config = BlindControlConfig.from_mapping(
        {**getattr(entry, "data", {}), **getattr(entry, "options", {})}
    )
    shadow = ShadowRuntime(config)
    coordinator = ShadowCoordinator(hass, entry, config, shadow)
    entry.runtime_data = BlindControlRuntimeData(
        config=config,
        shadow=shadow,
        coordinator=coordinator,
    )
    await coordinator.async_start()
    if hasattr(entry, "async_on_unload"):
        entry.async_on_unload(coordinator.stop)
    if hasattr(entry, "add_update_listener") and hasattr(entry, "async_on_unload"):
        entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Unload one entry and remove only observation listeners."""

    runtime_data = getattr(entry, "runtime_data", None)
    coordinator = getattr(runtime_data, "coordinator", None)
    if coordinator is not None:
        coordinator.stop()
    return True


async def _async_options_updated(hass: HomeAssistant, entry: BlindControlConfigEntry) -> None:
    """Recreate the read-only snapshot after an OptionsFlow change."""

    await hass.config_entries.async_reload(entry.domain, entry.entry_id)
