"""Read-only native Home Assistant status projection for AP2 Shadow mode."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BlindControlConfigEntry
from .shadow import ShadowSnapshot
from .ux_contract import AUTOMATION_PROJECTION_VERSION, build_automation_projection


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: BlindControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one stable, read-only status sensor for an AP2 Shadow entry."""

    async_add_entities([BlindControlStatusSensor(entry)])


class BlindControlStatusSensor(SensorEntity):
    """Expose the compact automation projection without an actuator surface."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(self, entry: BlindControlConfigEntry) -> None:
        """Bind the stable registry identity to the immutable ConfigEntry id."""

        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_shadow_status"

    @property
    def available(self) -> bool:
        """Only expose a state after the coordinator has evaluated a snapshot."""

        return self._snapshot is not None

    @property
    def native_value(self) -> str | None:
        """Use the master mode as the small automations-facing sensor state."""

        projection = self._projection
        value = projection.get("master_mode")
        return value if isinstance(value, str) else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Publish the shared, redacted automation contract as read-only attributes."""

        projection = self._projection
        if not projection:
            return {"contract_version": AUTOMATION_PROJECTION_VERSION}
        return {
            "contract_version": projection.get("version", AUTOMATION_PROJECTION_VERSION),
            **{key: value for key, value in projection.items() if key != "version"},
        }

    async def async_added_to_hass(self) -> None:
        """Write state only when the in-memory Shadow snapshot changes."""

        await super().async_added_to_hass()
        runtime_data = getattr(self._entry, "runtime_data", None)
        coordinator = getattr(runtime_data, "coordinator", None)
        if coordinator is not None:
            self.async_on_remove(coordinator.async_add_snapshot_listener(self.async_write_ha_state))

    @property
    def _snapshot(self) -> ShadowSnapshot | None:
        runtime_data = getattr(self._entry, "runtime_data", None)
        snapshot = getattr(runtime_data, "snapshot", None)
        return snapshot if isinstance(snapshot, ShadowSnapshot) else None

    @property
    def _projection(self) -> dict[str, object]:
        snapshot = self._snapshot
        return build_automation_projection(snapshot) if snapshot is not None else {}
