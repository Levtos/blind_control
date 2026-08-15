"""Bootstrap runtime for the Blind Control Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


@dataclass(frozen=True, slots=True)
class BlindControlRuntimeData:
    """Runtime state owned by one loaded Blind Control ConfigEntry."""

    phase: str = "bootstrap"


type BlindControlConfigEntry = ConfigEntry[BlindControlRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Prepare the integration without creating a shared data bucket."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Load one bootstrap ConfigEntry without creating entities or listeners."""

    entry.runtime_data = BlindControlRuntimeData()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlindControlConfigEntry) -> bool:
    """Unload one bootstrap entry without integration-owned cleanup."""

    return True
