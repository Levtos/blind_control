"""Administrative staging and the mandatory independent Legacy interlock."""

import asyncio
import importlib
import sys
from types import SimpleNamespace

import pytest
from test_apply import FakeHass, config_for, ready_inputs
from test_bootstrap import (
    _FakeConfigEntry,
    _FakeConnection,
    _FakeHomeAssistant,
    _home_assistant_imports,
)

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.config import BlindControlConfig
from custom_components.blind_control.operation import (
    legacy_writer_blocker,
    revision,
    runtime_matches,
    staged_config,
)
from custom_components.blind_control.shadow import ShadowRuntime


def request(config, mode="live", owner="blind_control", apply=False, **kwargs):
    return staged_config(
        config,
        {"runtime_mode": mode, "apply_owner": owner, "apply_enabled": apply},
        expected_revision=revision(config),
        confirmed=True,
        blocker=None,
        **kwargs,
    )


def test_complete_staging_preserves_config_and_requires_separate_arming():
    current = config_for("shadow", "legacy")
    with pytest.raises(ValueError, match="stage_live"):
        request(current, apply=True)
    staged = request(current)
    assert not staged.apply_enabled
    armed = request(staged, apply=True)
    assert armed.apply_enabled
    assert armed.input_bindings == current.input_bindings
    assert not request(armed, "shadow", "legacy").apply_enabled


def test_runtime_match_rejects_unloaded_or_changed_contract_config():
    config = config_for("live", "blind_control", apply_enabled=False)
    assert runtime_matches(config, config)
    assert not runtime_matches(config, None)
    changed = BlindControlConfig.from_mapping(
        {**config.to_mapping(), "core_contracts": {"opening": "fixture.opening"}}
    )
    assert not runtime_matches(changed, config)


@pytest.mark.parametrize("mode", ["shadow", "live"])
@pytest.mark.parametrize("owner", ["legacy", "blind_control"])
@pytest.mark.parametrize("enabled", [False, True])
def test_only_loaded_live_owner_off_can_arm(mode, owner, enabled):
    config = config_for(mode, owner, apply_enabled=enabled)
    if (mode, owner, enabled) == ("live", "blind_control", False):
        assert request(config, apply=True).apply_enabled
    else:
        with pytest.raises(ValueError):
            request(config, apply=True)


@pytest.mark.parametrize(
    "overrides",
    [
        {"expected_revision": "stale"},
        {"confirmed": False},
        {"blocker": "legacy_writer_not_disabled"},
    ],
)
def test_stale_unconfirmed_or_legacy_active_rejects_arming(overrides):
    config = config_for("live", "blind_control", apply_enabled=False)
    args = {"expected_revision": revision(config), "confirmed": True, "blocker": None, **overrides}
    with pytest.raises(ValueError):
        staged_config(
            config,
            {"runtime_mode": "live", "apply_owner": "blind_control", "apply_enabled": True},
            **args,
        )


@pytest.mark.parametrize(
    "disabled,state,service,blocked",
    [
        (None, "loaded", False, True),
        (None, "not_loaded", False, True),
        ("user", "loaded", False, True),
        ("user", "not_loaded", True, True),
        ("user", "not_loaded", False, False),
    ],
)
def test_legacy_interlock_at_actual_adapter(disabled, state, service, blocked):
    async def scenario():
        hass = FakeHass()
        hass.config_entries.async_entries = lambda domain: [
            SimpleNamespace(disabled_by=disabled, state=state)
        ]
        hass.services.has_service = lambda domain, name: service
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        result = await CoverApplyExecutor(hass, config, runtime).async_apply(
            runtime.evaluate(ready_inputs(), now=0), now=0
        )
        assert bool(legacy_writer_blocker(hass)) == blocked
        assert result.actuation_executed is not blocked
        assert len(hass.services.calls) == (0 if blocked else 1)

    asyncio.run(scenario())


def test_operation_websocket_is_admin_only_revokes_old_runtime_and_rejects_second_request():
    with _home_assistant_imports():
        integration = importlib.import_module("custom_components.blind_control")
        transport = importlib.import_module("custom_components.blind_control.websocket_api")
        hass = _FakeHomeAssistant()
        entry = _FakeConfigEntry("operator", data=config_for("shadow", "legacy").to_mapping())
        asyncio.run(integration.async_setup(hass, {}))
        asyncio.run(integration.async_setup_entry(hass, entry))
        hass.config_entries.async_entries = lambda domain: (
            [entry] if domain == "blind_control" else []
        )
        handler = next(
            item
            for item in sys.modules["homeassistant.components.websocket_api"].commands
            if item.websocket_schema["type"] == transport.SET_OPERATION
        )
        msg = {
            "id": 1,
            "expected_revision": revision(transport._entry_config(entry)),
            "operation": {
                "runtime_mode": "live",
                "apply_owner": "blind_control",
                "apply_enabled": False,
            },
        }
        denied = _FakeConnection(is_admin=False)
        asyncio.run(handler(hass, denied, msg))
        assert denied.errors[0][1] == "unauthorized"
        assert entry.runtime_data.shadow.active
        accepted = _FakeConnection(is_admin=True)
        asyncio.run(handler(hass, accepted, msg))
        assert not accepted.errors
        assert not entry.runtime_data.shadow.active
        assert hass.config_entries.updates[-1][1]["apply_enabled"] is False
        pending = _FakeConnection(is_admin=True)
        asyncio.run(handler(hass, pending, msg))
        assert pending.errors[0][1] == "not_loaded"
