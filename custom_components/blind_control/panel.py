"""Home Assistant custom-panel registration for the read-only Shadow UX."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

PANEL_URL_PATH = "blind-control"
STATIC_PREFIX = f"/{PANEL_URL_PATH}/frontend"
PANEL_JS = "blind-control-panel.js"


async def async_register_panel(hass: HomeAssistant) -> bool:
    """Serve and register the bundled custom element that receives ``hass``."""

    frontend_dir = Path(__file__).parent / "frontend"
    panel_js = frontend_dir / PANEL_JS
    if not panel_js.is_file():
        return False

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_PREFIX, str(frontend_dir), cache_headers=False)]
        )
    except (RuntimeError, ValueError):
        # Reloads retain the static registration; the panel metadata is refreshed below.
        pass

    panels = getattr(hass, "data", {}).get("frontend_panels", {})
    if PANEL_URL_PATH in panels:
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Blind Control",
        sidebar_icon="mdi:blinds",
        frontend_url_path=PANEL_URL_PATH,
        require_admin=True,
        config={
            "_panel_custom": {
                "name": "blind-control-panel",
                "embed_iframe": False,
                "trust_external": False,
                "js_url": f"{STATIC_PREFIX}/{PANEL_JS}",
            }
        },
    )
    return True
