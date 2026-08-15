"""Bootstrap runtime for the Blind Control Home Assistant integration.

AP1 deliberately owns no entity platform, service, websocket command, or
actuation path.  The entry is kept in ``hass.data`` so setup and unload are
reproducible while the inventory and contract decisions are completed.
"""

from __future__ import annotations

from typing import Any

from .const import DOMAIN


async def async_setup(hass: Any, config: dict[str, Any]) -> bool:
    """Prepare the integration namespace without registering a write surface."""

    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    """Load one bootstrap ConfigEntry without creating entities or listeners."""

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "entry": entry,
        "runtime": "bootstrap",
    }
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    """Unload one bootstrap entry and leave no runtime state behind."""

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
