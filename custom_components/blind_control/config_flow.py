"""Minimal ConfigEntry flow for the Blind Control AP1 bootstrap."""

from __future__ import annotations

from typing import Any

from .const import DOMAIN

try:  # Home Assistant is available only when the integration is installed.
    import voluptuous as vol
    from homeassistant.config_entries import ConfigFlow

    HA_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised by the stdlib-only checks
    HA_AVAILABLE = False

    class ConfigFlow:  # type: ignore[no-redef]
        """Import fallback used for syntax and boundary checks outside HA."""

        pass


if HA_AVAILABLE:

    class BlindControlConfigFlow(ConfigFlow, domain=DOMAIN):
        """Create an empty, non-actuating AP1 entry."""

        VERSION = 1

        async def async_step_user(self, user_input: dict[str, Any] | None = None):
            if user_input is not None:
                return self.async_create_entry(title="Blind Control", data={})

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
            )

else:

    class BlindControlConfigFlow(ConfigFlow):  # type: ignore[no-redef]
        """Fallback class for environments without Home Assistant imports."""

        VERSION = 1
