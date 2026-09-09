"""Consumer quality regressions and conformance against the pinned upstream API."""

import importlib
import os
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from test_apply import fresh, ready_inputs

from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.core_inputs import CoreInputs, field_observation
from custom_components.blind_control.engine import DecisionEngine


@pytest.mark.parametrize(
    "changes",
    [
        {"freshness": "stale"},
        {"freshness": "restored"},
        {"freshness": "unknown"},
        {"quality_status": "conflict"},
        {"quality_status": "degraded"},
        {"health": "blocked"},
        {"state": "invalid"},
        {"state": "unknown"},
        {"state": "unavailable"},
        {"value": float("nan")},
        {"value": True},
    ],
)
def test_upstream_negative_quality_never_becomes_fresh(changes):
    field = SimpleNamespace(
        value=20, state="valid", freshness="fresh", quality_status="good", health="healthy"
    )
    for key, value in changes.items():
        setattr(field, key, value)
    assert not field_observation(field).usable


def test_unselected_fallback_is_explicit_and_selected_missing_api_blocks():
    inputs = ready_inputs(outdoor_temperature=fresh(18))
    config = BlindControlConfig.defaults()
    bridge = CoreInputs(SimpleNamespace(data={}), config, "fixture", lambda: None)
    assert bridge.apply(inputs) is inputs
    assert set(bridge.status.values()) == {"compatibility_fallback_unselected"}
    bridge.config = replace(config, core_contracts=(("weather_environment", "fixture.weather"),))
    assert not bridge.apply(inputs).outdoor_temperature.usable
    assert not bridge.apply(inputs).outdoor_lux.usable
    assert bridge.apply(inputs).cover_position is inputs.cover_position


def test_config_v6_roundtrip_and_native_options_preserve_core_selection():
    config = BlindControlConfig.from_mapping(
        {"core_contracts": {"opening": "fixture.opening"}, "core_contract_profile": "eltern"}
    )
    assert BlindControlConfig.from_mapping(config.to_mapping()).to_mapping() == config.to_mapping()
    assert BlindControlConfig.from_mapping({"config_version": 6}).core_contracts == ()


@pytest.fixture
def upstream(monkeypatch):
    root = os.environ.get("BLIND_CONTROL_CORE_TEST_PATH")
    if not root:
        pytest.skip("Set BLIND_CONTROL_CORE_TEST_PATH to the pinned Core Contracts checkout")
    package = ModuleType("custom_components.benni_core_contracts")
    package.__path__ = [str(Path(root) / "custom_components/benni_core_contracts")]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    return SimpleNamespace(
        **{
            name: importlib.import_module(f"{package.__name__}.{name}")
            for name in (
                "consumer_api",
                "contracts",
                "graph",
                "models",
                "quality",
                "registry",
                "registry_service",
            )
        }
    )


def test_real_registry_api_subscription_quality_unload_and_reconnect(upstream):
    """Exercise real v0.2.1 DTOs, declarations, graph events and close behavior."""
    u = upstream
    now = datetime.now(UTC)
    profile = u.models.ProfileId.BENNI
    bindings = tuple(
        u.models.SourceBinding(
            binding_id=f"fixture_{field}",
            source_id=f"fixture_{field}",
            entity_id=f"sensor.fixture_{field}",
            field=field,
            capability="opening",
            profile_id=profile,
        )
        for field in ("opening_state", "available")
    )
    fusions = tuple(
        u.models.Fusion(
            fusion_id=f"fusion_{b.field}",
            contract_id="fixture.opening",
            field=b.field,
            input_binding_ids=(b.binding_id,),
            strategy="first_healthy",
        )
        for b in bindings
    )
    payload = u.registry.RegistryPayload(
        profile=profile,
        bindings=bindings,
        fusions=fusions,
        contract_instances=(
            {
                "contract_id": "fixture.opening",
                "schema_id": "opening",
                "schema_version": 1,
                "profile": "benni",
            },
        ),
    )
    registry = u.contracts.default_schema_registry()
    graph = u.graph.SignalGraph(registry=registry, now_factory=lambda: now)
    for b in bindings:
        graph.add_binding(b)
    graph.add_fusions(fusions)

    def ingest(opening):
        for b, value in zip(bindings, (opening, True), strict=True):
            graph.ingest(
                b.binding_id,
                u.models.RawObservation(
                    source_id=b.source_id,
                    entity_id=b.entity_id,
                    value=value,
                    evidence=u.quality.TemporalEvidence(
                        received_at=now,
                        origin=u.quality.FreshnessOrigin.DEVICE_TIMESTAMP,
                        device_timestamp=now,
                    ),
                ),
                now=now,
            )
        graph.evaluate_contract("fixture.opening", "opening", schema_version=1, now=now)

    ingest("closed")
    runtime = u.registry_service.RegistryRuntime(schema_registry=registry)
    runtime.activate(
        u.registry.RegistryRevision(
            id="fixture-revision",
            revision=1,
            profile=profile,
            schema_version=1,
            payload=payload,
            status=u.registry.RevisionStatus.ACTIVE,
            created_at=now,
            activated_at=now,
        ),
        graph,
    )
    api = u.consumer_api.ConsumerApi(runtime, now_factory=lambda: now)
    hass = SimpleNamespace(data={"benni_core_contracts": {"_consumer_api": api}})
    config = BlindControlConfig.from_mapping({"core_contracts": {"opening": "fixture.opening"}})
    events = []
    bridge = CoreInputs(hass, config, "fixture-blind", lambda: events.append(True))
    inputs = ready_inputs()
    assert bridge.apply(inputs).opening_state.value == "closed"
    assert api.requirements_for("fixture-blind")[0].expected_schema_version == 1
    assert api.subscription_count("fixture-blind") == 1
    ingest("open")
    assert events
    result = bridge.apply(inputs)
    assert result.opening_state.usable and result.opening_state.value == "open"
    decision = DecisionEngine(config).evaluate(result)
    assert decision.effective_target >= inputs.cover_position.value
    ingest("unknown")
    assert not bridge.apply(inputs).opening_state.usable
    api.close()
    assert not bridge.apply(inputs).opening_state.usable
    new_api = u.consumer_api.ConsumerApi(runtime, now_factory=lambda: now)
    hass.data["benni_core_contracts"]["_consumer_api"] = new_api
    ingest("closed")
    assert bridge.apply(inputs).opening_state.usable
    previous = bridge.apply(inputs).opening_state
    # Same value, new owner-valid device report: never age by last_real_change.
    now += timedelta(hours=2)
    ingest("closed")
    repeated = bridge.apply(inputs).opening_state
    assert repeated.usable and repeated.value == previous.value
    assert repeated.source_revision != previous.source_revision
    assert repeated.timestamp_basis == "owner_field_quality_no_consumer_reaging"
    assert repeated.updated_at is None  # DTO does not expose an effective measurement time.
    bridge.stop()
    assert new_api.subscription_count("fixture-blind") == 0
    new_api.close()
