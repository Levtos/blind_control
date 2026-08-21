"""Read-only native Home Assistant status projection for AP2 Shadow mode."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfIrradiance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BlindControlConfigEntry
from .const import DOMAIN
from .open_meteo import (
    OPEN_METEO_MODEL,
    OPEN_METEO_PROVIDER,
    OPEN_METEO_UPDATE_INTERVAL_SECONDS,
)
from .radiation_provider import OpenMeteoRadiationCoordinator
from .shadow import ShadowSnapshot
from .ux_contract import AUTOMATION_PROJECTION_VERSION, build_automation_projection


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: BlindControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one stable, read-only status sensor for an AP2 Shadow entry."""

    provider = entry.runtime_data.radiation_provider
    entities: list[SensorEntity] = [BlindControlStatusSensor(entry)]
    if provider is not None:
        entities.extend(
            (
                BlindControlRadiationSensor(
                    entry,
                    provider,
                    name="Blind Control DNI Instant",
                    unique_id="blind_control_dni_instant",
                    data_attribute="direct_normal_irradiance",
                ),
                BlindControlRadiationSensor(
                    entry,
                    provider,
                    name="Blind Control Diffuse Radiation Instant",
                    unique_id="blind_control_diffuse_radiation_instant",
                    data_attribute="diffuse_radiation",
                ),
            )
        )
    async_add_entities(entities)


def _device_info(entry: BlindControlConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Blind Control",
        manufacturer="Levtos",
        model="Shadow",
    )


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
        self._attr_device_info = _device_info(entry)

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


class BlindControlRadiationSensor(
    CoordinatorEntity[OpenMeteoRadiationCoordinator],
    SensorEntity,
):
    """Expose one value from the shared read-only provider response."""

    _attr_has_entity_name = False
    _attr_device_class = SensorDeviceClass.IRRADIANCE
    _attr_native_unit_of_measurement = UnitOfIrradiance.WATTS_PER_SQUARE_METER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: BlindControlConfigEntry,
        coordinator: OpenMeteoRadiationCoordinator,
        *,
        name: str,
        unique_id: str,
        data_attribute: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = _device_info(entry)
        self._data_attribute = data_attribute

    @property
    def available(self) -> bool:
        """Retain degraded fresh data but never expose stale data as available."""

        return self.coordinator.data is not None and self.coordinator.provider_status() != "stale"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        return float(getattr(data, self._data_attribute)) if data is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        return {
            "provider": OPEN_METEO_PROVIDER,
            "model": OPEN_METEO_MODEL,
            "last_successful_update": data.fetched_at.isoformat() if data else None,
            "data_timestamp": data.data_timestamp if data else None,
            "update_interval": OPEN_METEO_UPDATE_INTERVAL_SECONDS,
            "provider_status": self.coordinator.provider_status(),
        }
