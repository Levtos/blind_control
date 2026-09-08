from __future__ import annotations

import asyncio
import sys
import types
import unittest
from dataclasses import replace
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "blind_control"
if "custom_components.blind_control" not in sys.modules:
    package = types.ModuleType("custom_components.blind_control")
    package.__path__ = [str(PACKAGE)]
    sys.modules["custom_components.blind_control"] = package

from custom_components.blind_control.apply import CoverApplyExecutor  # noqa: E402
from custom_components.blind_control.config import BlindControlConfig  # noqa: E402
from custom_components.blind_control.contracts import (  # noqa: E402
    BlindControlInputs,
    InputObservation,
    InputQuality,
)
from custom_components.blind_control.shadow import ShadowRuntime  # noqa: E402


def fresh(value, source: str = "owner"):
    return InputObservation(value=value, source=source, quality=InputQuality.FRESH)


def ready_inputs(**changes) -> BlindControlInputs:
    values = {
        "bio_state": fresh("awake"),
        "activity_state": fresh("none"),
        "day_state": fresh("forenoon"),
        "day_context": fresh("weekday"),
        "away": fresh(False),
        "private_time": fresh(False),
        "privacy": fresh(False),
        "opening_state": fresh("closed"),
        "opening_safe_for_blind": fresh(True),
        "cover_available": fresh(True),
        "cover_ready": fresh(True),
        "cover_position": fresh(42.0),
        "outdoor_lux": fresh(12_000.0),
        "lux_trend": fresh(0.0),
        "sun_elevation": fresh(30.0),
        "sun_azimuth": fresh(124.0),
        "expected_direct_radiation": fresh(400.0),
        "expected_diffuse_radiation": fresh(50.0),
        "cloud_cover": fresh(10.0),
        "indoor_temperature": fresh(22.0),
        "outdoor_temperature": fresh(20.0),
    }
    values.update(changes)
    return BlindControlInputs(**values)


class FakeServices:
    def has_service(self, domain, service):
        return False

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, dict[str, object], bool]] = []
        self.background_errors: list[Exception] = []
        self.tasks: list[asyncio.Task] = []

    async def async_call(self, domain, service, data, *, blocking=False):
        self.calls.append((domain, service, data, blocking))
        if blocking:
            await self._handler()
        else:
            # HA schedules the handler and catches/logs failures in that task.
            self.tasks.append(asyncio.create_task(self._catch_handler_error()))

    async def _handler(self):
        await asyncio.sleep(0)
        if self.fail:
            raise RuntimeError("redacted service failure")

    async def _catch_handler_error(self):
        try:
            await self._handler()
        except Exception as error:
            self.background_errors.append(error)


class FakeHass:
    def __init__(self, *, fail: bool = False) -> None:
        self.services = FakeServices(fail=fail)
        from types import SimpleNamespace

        self.config_entries = SimpleNamespace(async_entries=lambda domain: [])


def config_for(mode: str, owner: str, *, apply_enabled: bool = True) -> BlindControlConfig:
    return BlindControlConfig.from_mapping(
        {
            "runtime_mode": mode,
            "apply_owner": owner,
            "apply_enabled": apply_enabled,
            "input_bindings": {"cover_position": "cover.contract_blind"},
            "apply_cooldown_seconds": 60,
            "position_tolerance": 1,
        }
    )


class ApplyExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_exactly_one_gate_combination_reaches_the_writer(self) -> None:
        combinations = [
            (mode, owner, enabled)
            for mode in ("shadow", "live")
            for owner in ("legacy", "blind_control")
            for enabled in (False, True)
        ]

        for mode, owner, enabled in combinations:
            with self.subTest(mode=mode, owner=owner, enabled=enabled):
                config = config_for(mode, owner, apply_enabled=enabled)
                runtime = ShadowRuntime(config)
                runtime.on_restart(42)
                hass = FakeHass()
                snapshot = runtime.evaluate(ready_inputs(), now=20)

                result = await CoverApplyExecutor(hass, config, runtime).async_apply(
                    snapshot, now=20
                )

                expected = mode == "live" and owner == "blind_control" and enabled
                self.assertEqual(len(hass.services.calls), int(expected))
                self.assertEqual(result.actuation_executed, expected)

    async def test_shadow_has_no_writer_even_with_ready_intent(self) -> None:
        config = config_for("shadow", "blind_control")
        runtime = ShadowRuntime(config)
        snapshot = runtime.evaluate(ready_inputs(), now=20)
        hass = FakeHass()

        result = await CoverApplyExecutor(hass, config, runtime).async_apply(snapshot, now=20)

        self.assertTrue(result.shadow_only)
        self.assertFalse(result.write_path_reachable)
        self.assertFalse(result.actuation_executed)
        self.assertEqual(hass.services.calls, [])

    async def test_live_requires_exclusive_owner_and_restart_baseline(self) -> None:
        config = config_for("live", "legacy")
        runtime = ShadowRuntime(config)
        owner_blocked = runtime.evaluate(ready_inputs(), now=20)
        restart_blocked = ShadowRuntime(config_for("live", "blind_control")).evaluate(
            ready_inputs(), now=20, runtime_ready=False
        )

        self.assertEqual(owner_blocked.trace.apply.reason, "exclusive_apply_owner_not_confirmed")
        self.assertFalse(owner_blocked.write_path_reachable)
        self.assertEqual(restart_blocked.trace.apply.reason, "restart_baseline_pending")
        self.assertFalse(restart_blocked.write_path_reachable)

    async def test_live_dispatches_once_and_own_write_does_not_create_override(self) -> None:
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        snapshot = runtime.evaluate(ready_inputs(), now=20)
        hass = FakeHass()
        executor = CoverApplyExecutor(hass, config, runtime)

        applied = await executor.async_apply(snapshot, now=20)
        runtime.observe_cover_position(100, now=21)
        runtime.observe_cover_position(100, now=23)
        stable = runtime.evaluate(replace(ready_inputs(), cover_position=fresh(100.0)), now=24)
        stable_result = await executor.async_apply(stable, now=24)

        self.assertEqual(len(hass.services.calls), 1)
        self.assertEqual(hass.services.calls[0][0:2], ("cover", "set_cover_position"))
        self.assertEqual(hass.services.calls[0][2]["position"], 100.0)
        self.assertTrue(hass.services.calls[0][3])
        self.assertTrue(applied.actuation_executed)
        self.assertEqual(applied.trace.apply.status, "applied")
        self.assertFalse(runtime.override.active)
        self.assertEqual(stable.trace.apply.status, "stable")
        self.assertFalse(stable_result.actuation_executed)
        self.assertEqual(len(hass.services.calls), 1)

    async def test_owned_movement_guard_closes_when_target_is_observed(self) -> None:
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        snapshot = runtime.evaluate(ready_inputs(), now=20)
        hass = FakeHass()

        await CoverApplyExecutor(hass, config, runtime).async_apply(snapshot, now=20)
        runtime.observe_cover_position(70, now=21)
        runtime.observe_cover_position(100, now=22)
        runtime.observe_cover_position(100, now=24)
        runtime.observe_cover_position(80, now=25)
        self.assertFalse(runtime.override.active)
        runtime.observe_cover_position(80, now=27)

        self.assertTrue(runtime.override.active)
        self.assertEqual(runtime.override.baseline, 100)
        self.assertEqual(runtime.override.observed_position, 80)

    async def test_manual_override_blocks_automatic_write_but_not_safety(self) -> None:
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        runtime.observe_cover_position(60, now=10)
        runtime.observe_cover_position(60, now=12)
        hass = FakeHass()
        executor = CoverApplyExecutor(hass, config, runtime)

        held = runtime.evaluate(ready_inputs(), now=20)
        await executor.async_apply(held, now=20)
        safety = runtime.evaluate(
            ready_inputs(opening_state=fresh("open")),
            now=21,
        )
        applied = await executor.async_apply(safety, now=21)

        self.assertEqual(held.trace.apply.status, "manual_hold")
        self.assertEqual(safety.trace.apply.status, "safety_ready")
        self.assertTrue(applied.actuation_executed)
        self.assertEqual(len(hass.services.calls), 1)

    async def test_failed_write_retains_attribution_and_blocks_automatic_retry(self) -> None:
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        failing_hass = FakeHass(fail=True)
        snapshot = runtime.evaluate(ready_inputs(), now=20)

        failed = await CoverApplyExecutor(failing_hass, config, runtime).async_apply(
            snapshot, now=20
        )
        runtime.observe_cover_position(60, now=21)

        self.assertEqual(failed.trace.apply.status, "error")
        self.assertFalse(runtime.override.active)
        retry = runtime.evaluate(ready_inputs(), now=22)
        self.assertEqual(retry.trace.apply.status, "blocked")

    async def test_cooldown_dispatches_only_the_latest_target(self) -> None:
        config = config_for("live", "blind_control")
        runtime = ShadowRuntime(config)
        runtime.on_restart(42)
        hass = FakeHass()
        executor = CoverApplyExecutor(hass, config, runtime)

        first = runtime.evaluate(ready_inputs(), now=20)
        await executor.async_apply(first, now=20)
        runtime.observe_cover_position(100, now=21)
        runtime.observe_cover_position(100, now=23)
        # The entering heat has not completed its environmental dwell yet.
        pending_heat = runtime.evaluate(
            ready_inputs(
                indoor_temperature=fresh(27.0),
                outdoor_temperature=fresh(34.0),
            ),
            now=30,
        )
        glare = runtime.evaluate(
            ready_inputs(activity_state=fresh("pc")),
            now=40,
        )
        released = runtime.evaluate(
            ready_inputs(activity_state=fresh("pc")),
            now=81,
        )
        await executor.async_apply(released, now=81)

        self.assertNotIn("heat_protection", pending_heat.trace.winner_keys)
        self.assertTrue(pending_heat.environment["heat"]["pending"])
        self.assertEqual(glare.trace.apply.cooldown_pending_target, 75.0)
        self.assertEqual([call[2]["position"] for call in hass.services.calls], [100.0, 75.0])


if __name__ == "__main__":
    unittest.main()
