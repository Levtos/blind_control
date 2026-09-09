"""Core State owns the phase; Blind Control owns the privacy profile mapping."""

import asyncio
from dataclasses import replace

import pytest
from test_apply import FakeHass, config_for, fresh, ready_inputs

from custom_components.blind_control.apply import CoverApplyExecutor
from custom_components.blind_control.contracts import InputObservation, InputQuality
from custom_components.blind_control.engine import DecisionEngine
from custom_components.blind_control.privacy import DAY_PHASES, PRIVACY_PHASES
from custom_components.blind_control.shadow import ShadowRuntime
from custom_components.blind_control.ux_contract import build_ux_snapshot


@pytest.mark.parametrize("phase", sorted(DAY_PHASES))
@pytest.mark.parametrize("old_privacy", [True, False, None])
def test_phase_contract_ignores_retired_boolean_and_lux(phase, old_privacy):
    inputs = ready_inputs(
        day_state=fresh(phase),
        privacy=fresh(old_privacy),
        sun_elevation=fresh(-2),
        outdoor_lux=InputObservation(quality=InputQuality.UNAVAILABLE),
    )
    trace = DecisionEngine().evaluate(inputs)
    privacy = next(item for item in trace.candidates if item.key == "privacy")
    assert privacy.active is (phase in PRIVACY_PHASES)
    assert trace.effective_target == (40 if phase in PRIVACY_PHASES else None)
    fact = next(item for item in trace.decision.evidence if item.key == "privacy")
    assert fact.value is (phase in PRIVACY_PHASES)


@pytest.mark.parametrize("bio,target", [("sleep", 5), ("provisional_sleep", 5), ("waking", 100)])
def test_evening_privacy_context_clamp(bio, target):
    trace = DecisionEngine().evaluate(
        ready_inputs(
            day_state=fresh("late_evening"),
            bio_state=fresh(bio),
            sun_elevation=fresh(-2),
        )
    )
    assert trace.effective_target == target
    privacy = next(item for item in trace.decision.contributions if item.feature == "privacy")
    assert privacy.status == ("paused" if bio == "waking" else "active")


@pytest.mark.parametrize(
    "quality", [InputQuality.STALE, InputQuality.UNAVAILABLE, InputQuality.CONFLICT]
)
def test_lost_phase_holds_opening_but_sleep_can_close(quality):
    inputs = ready_inputs(day_state=InputObservation(value="evening", quality=quality))
    trace = DecisionEngine().evaluate(inputs)
    assert trace.effective_target is None or trace.effective_target <= 42
    assert any(item.feature == "privacy" for item in trace.decision.issues)
    assert (
        DecisionEngine().evaluate(replace(inputs, bio_state=fresh("sleep"))).effective_target == 5
    )


def test_no_target_is_idle_with_positive_safety_and_never_dispatches():
    async def scenario():
        config = config_for("live", "blind_control", apply_enabled=True)
        runtime = ShadowRuntime(config)
        inputs = ready_inputs(sun_elevation=fresh(-2))
        snapshot = runtime.evaluate(inputs)
        assert snapshot.trace.safety.status == "ready"
        assert snapshot.trace.apply.status == "idle"
        assert snapshot.trace.decision.safety.block_direction is None
        hass = FakeHass()
        result = await CoverApplyExecutor(hass, config, runtime).async_apply(snapshot)
        assert not result.actuation_executed
        assert not hass.services.calls
        ux = build_ux_snapshot(snapshot, config)
        assert ux["overview"]["household"]["privacy"] is False

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "key,value", [("cover_ready", False), ("cover_available", False), ("opening_state", "unknown")]
)
def test_no_target_does_not_hide_real_safety_blockers(key, value):
    trace = DecisionEngine().evaluate(ready_inputs(sun_elevation=fresh(-2), **{key: fresh(value)}))
    assert trace.safety.status == "blocked"
    assert trace.apply.status == "blocked"


def test_privacy_snapshot_matches_decision_and_sleep_replaces_pending():
    config = config_for("live", "blind_control", apply_enabled=True)
    runtime = ShadowRuntime(config)
    evening = ready_inputs(day_state=fresh("late_evening"), sun_elevation=fresh(-2))
    first = runtime.evaluate(evening)
    second = runtime.evaluate(replace(evening, bio_state=fresh("sleep")))
    assert first.trace.effective_target == 40
    assert second.trace.effective_target == 5
    assert second.inputs["privacy"]["value"] is True
    assert first.trace.decision.decision_generation < second.trace.decision.decision_generation


def test_latest_sleep_dispatches_and_replaced_privacy_never_writes():
    async def scenario():
        config = config_for("live", "blind_control", apply_enabled=True)
        runtime = ShadowRuntime(config)
        runtime.on_restart(100)
        evening = ready_inputs(
            day_state=fresh("late_evening"), sun_elevation=fresh(-2), cover_position=fresh(100)
        )
        old = runtime.evaluate(evening, now=10)
        latest = runtime.evaluate(replace(evening, bio_state=fresh("sleep")), now=11)
        hass = FakeHass()
        writer = CoverApplyExecutor(hass, config, runtime)
        assert not (await writer.async_apply(old, now=11)).actuation_executed
        result = await writer.async_apply(latest, now=11)
        assert result.actuation_executed
        assert len(hass.services.calls) == 1
        assert hass.services.calls[0][2]["position"] == 5
        assert hass.services.calls[0][3] is True

    asyncio.run(scenario())
