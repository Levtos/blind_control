"""Consumer API boundary for existing Core Contracts v1 schemas.

No registry internals, owner calculations, entity discovery, or TTL overrides.
Unselected schema gaps retain the explicit compatibility adapter. Once selected,
an unavailable contract fails closed, including upstream unload and deletion.
"""

from dataclasses import replace
from math import isfinite

from .contracts import InputObservation, InputQuality

FIELDS = {
    "opening": {"opening_state": "opening_state"},
    "room_climate": {"indoor_temperature": "temperature"},
    "weather_environment": {
        "outdoor_temperature": "outdoor_temperature",
        "outdoor_lux": "illuminance",
    },
}


def _value(enum):
    return getattr(enum, "value", enum)


def field_observation(field, *, opening=False):
    """Preserve upstream quality and freshness; never re-age a snapshot locally."""
    quality = InputQuality.UNKNOWN
    if _value(field.quality_status) == "conflict" or _value(field.state) == "invalid":
        quality = InputQuality.CONFLICT
    elif _value(field.freshness) == "stale":
        quality = InputQuality.STALE
    elif _value(field.state) == "unavailable":
        quality = InputQuality.UNAVAILABLE
    elif (
        _value(field.state) == "valid"
        and _value(field.freshness) == "fresh"
        and _value(field.quality_status) == "good"
        and _value(field.health) == "healthy"
    ):
        quality = InputQuality.FRESH
    value = field.value
    valid = value in {"closed", "tilted", "open"} if opening and isinstance(value, str) else False
    if not opening:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
    if quality == InputQuality.FRESH and not valid:
        quality = InputQuality.CONFLICT
    return InputObservation(
        value=value if quality == InputQuality.FRESH else None,
        quality=quality,
        source="core_contracts",
        owner="core_contracts",
        timestamp_basis="owner_field_quality_no_consumer_reaging",
        source_revision=(
            f"{field.registry_revision}:{field.graph_revision}"
            if hasattr(field, "registry_revision") and hasattr(field, "graph_revision")
            else None
        ),
        reason="core_consumer_api_field_contract",
    )


class CoreInputs:
    """Optional integration lifecycle with declared, version-pinned requirements."""

    def __init__(self, hass, config, consumer_id, on_change):
        self.hass, self.config = hass, config
        self.consumer_id, self.on_change = consumer_id, on_change
        self.api = None
        self.status = {}

    def stop(self):
        if self.api is not None:
            try:
                self.api.unregister_consumer(self.consumer_id)
            except Exception:  # Upstream close already removes subscriptions/declarations.
                pass
            self.api = None

    def _connect(self):
        registry = getattr(self.hass, "data", {}).get("benni_core_contracts", {})
        api = registry.get("_consumer_api")
        if api is self.api:
            return api
        self.stop()
        if api is None:
            return None
        from custom_components.benni_core_contracts.consumer_api import ConsumerRequirement
        from custom_components.benni_core_contracts.models import ProfileId

        requirements = tuple(
            ConsumerRequirement.contract(
                contract_id,
                profile=ProfileId(self.config.core_contract_profile),
                schema_id=schema,
                expected_schema_version=1,
                required_fields=(*FIELDS[schema].values(), "available"),
            )
            for schema, contract_id in self.config.core_contracts
        )
        api.register_consumer(self.consumer_id, requirements)
        self.api = api
        for _, contract_id in self.config.core_contracts:
            api.subscribe(
                self.consumer_id,
                lambda _update: self.on_change(),
                contract_id=contract_id,
                profile=self.config.core_contract_profile,
            )
        return api

    def apply(self, inputs):
        updates = {}
        selected = dict(self.config.core_contracts)
        self.status = {schema: "compatibility_fallback_unselected" for schema in FIELDS}
        if not selected:
            return inputs
        try:
            api = self._connect()
        except (
            Exception
        ):  # Optional upstream lifecycle/API errors fail closed without private logs.
            api = None
        for schema, contract_id in selected.items():
            status = "runtime_not_ready"
            snapshot = None
            if api is not None:
                try:
                    result = api.lookup_contract(
                        contract_id,
                        profile=self.config.core_contract_profile,
                        schema_id=schema,
                        expected_schema_version=1,
                        required_fields=(*FIELDS[schema].values(), "available"),
                    )
                    status = _value(result.status)
                    if status in {"healthy", "degraded"}:
                        snapshot = result.snapshot
                except Exception:  # Includes typed ConsumerApiError after upstream unload.
                    status = "runtime_not_ready"
            for key, name in FIELDS[schema].items():
                observation = InputObservation(
                    quality=InputQuality.UNKNOWN,
                    source="core_contracts",
                    reason="core_contract_unavailable_or_incompatible",
                )
                if snapshot is not None:
                    available = snapshot.field("available")
                    if (
                        available.value is True
                        and _value(available.state) == "valid"
                        and _value(available.freshness) == "fresh"
                        and _value(available.quality_status) == "good"
                        and _value(available.health) == "healthy"
                    ):
                        observation = field_observation(
                            snapshot.field(name), opening=key == "opening_state"
                        )
                updates[key] = observation
            self.status[schema] = status
        return replace(inputs, **updates)
