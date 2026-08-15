"""Minimal ConfigEntry flow for the Blind Control AP1 bootstrap."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN


class BlindControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Create one empty, non-actuating AP1 entry."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Blind Control", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )
