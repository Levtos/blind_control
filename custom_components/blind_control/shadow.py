"""Shadow runtime and snapshot contract; no executable write path is exposed."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import BlindControlConfig
from .contracts import BlindControlInputs, DecisionTrace, ManualOverride
from .cooldown import CooldownTracker
from .engine import DecisionEngine
from .override import OverrideTracker
from .shadow_diff import ShadowDiff, compare_legacy_snapshot

SHADOW_CONTRACT_VERSION = "blind_control.shadow.v1"


@dataclass(frozen=True, slots=True)
class ShadowSnapshot:
    """Read-only evidence of one complete decision evaluation."""

    version: str
    evaluated_at: datetime
    inputs: dict[str, object]
    trace: DecisionTrace
    diffs: tuple[ShadowDiff, ...] = ()
    shadow_only: bool = True
    actuation_executed: bool = False
    write_path_reachable: bool = False

    @property
    def effective_target(self) -> float | None:
        return self.trace.effective_target

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "evaluated_at": self.evaluated_at.isoformat(),
            "inputs": self.inputs,
            "trace": self.trace.as_dict(),
            "diffs": [diff.as_dict() for diff in self.diffs],
            "shadow_only": self.shadow_only,
            "actuation_executed": self.actuation_executed,
            "write_path_reachable": self.write_path_reachable,
        }

    def debug_payload(self) -> dict[str, object]:
        """Return the copyable diagnostic payload without private topology."""

        payload = self.as_dict()
        payload["inputs"] = {
            key: value for key, value in self.inputs.items() if not _is_sensitive_key(key)
        }
        return payload


class ShadowRuntime:
    """Connect contracts, decision engine, override and cooldown in memory only."""

    def __init__(self, config: BlindControlConfig | None = None) -> None:
        self.config = config or BlindControlConfig.defaults()
        self.engine = DecisionEngine(self.config)
        self.override_tracker = OverrideTracker.from_config(self.config)
        self.cooldown_tracker = CooldownTracker(tolerance=self.config.position_tolerance)

    @property
    def override(self) -> ManualOverride:
        return self.override_tracker.override

    def evaluate(
        self,
        inputs: BlindControlInputs,
        *,
        evaluated_at: datetime | None = None,
        now: float = 0.0,
        legacy_snapshot: Mapping[str, object] | None = None,
    ) -> ShadowSnapshot:
        if inputs.bio_state.usable and str(inputs.bio_state.value).lower() == "waking":
            if self.override.active:
                self.override_tracker.clear()
        trace = self.engine.evaluate(
            inputs,
            override=self.override,
            now=now,
            cooldown=self.cooldown_tracker,
        )
        return ShadowSnapshot(
            version=SHADOW_CONTRACT_VERSION,
            evaluated_at=evaluated_at or datetime.now(UTC),
            inputs=inputs.as_dict(),
            trace=trace,
            diffs=compare_legacy_snapshot(legacy_snapshot, trace),
        )

    def update_config(
        self,
        config: BlindControlConfig,
        inputs: BlindControlInputs,
        *,
        evaluated_at: datetime | None = None,
        now: float = 0.0,
    ) -> ShadowSnapshot:
        """Apply configuration in memory and immediately recompute the snapshot."""

        self.config = config
        self.engine = DecisionEngine(config)
        self.override_tracker.tolerance = config.position_tolerance
        self.on_configuration_change()
        return self.evaluate(inputs, evaluated_at=evaluated_at, now=now)

    def on_restart(self, position: float | None) -> ManualOverride:
        return self.override_tracker.on_restart(position)

    def on_configuration_change(self, position: float | None = None) -> ManualOverride:
        return self.override_tracker.on_configuration_change(position)

    def begin_own_write(
        self, target: float, *, now: float = 0.0, grace_seconds: float = 10.0
    ) -> None:
        self.override_tracker.begin_own_write(
            target,
            now=now,
            grace_seconds=grace_seconds,
        )

    def observe_cover_position(
        self,
        position: float | None,
        *,
        source: str = "cover_observation",
        now: float = 0.0,
        observed_at: datetime | None = None,
    ) -> ManualOverride:
        return self.override_tracker.observe_position(
            position,
            source=source,
            now=now,
            observed_at=observed_at,
        )

    def clear_override(self) -> ManualOverride:
        return self.override_tracker.clear()


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return (
        normalized in {"token", "secret", "password", "private_url", "supervisor_token"}
        or normalized.endswith("_token")
        or normalized.endswith("_secret")
        or normalized.endswith("_password")
        or normalized.endswith("_url")
    )
