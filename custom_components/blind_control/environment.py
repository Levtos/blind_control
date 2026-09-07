"""Small latest-state environmental hysteresis/debounce, without timers or targets."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EnvironmentalTransition:
    """A Schmitt input followed by an asymmetric, continuously observed dwell."""

    active: bool = False
    pending: bool | None = None
    since: float | None = None

    def observe(
        self, desired: bool, *, now: float, enter: float, exit: float, valid: bool = True
    ) -> bool:
        if not valid or desired == self.active:
            self.pending = None
            self.since = None
        else:
            if self.pending != desired or self.since is None or now < self.since:
                self.pending = desired
                self.since = now
            if now - self.since >= (enter if desired else exit):
                self.active = desired
                self.pending = None
                self.since = None
        return self.active if valid else False

    def as_dict(self) -> dict[str, object]:
        return {"active": self.active, "pending": self.pending, "since": self.since}


@dataclass(slots=True)
class EnvironmentalState:
    """Only environmental eligibility is retained; activity and targets stay current."""

    heat: EnvironmentalTransition = field(default_factory=EnvironmentalTransition)
    glare: EnvironmentalTransition = field(default_factory=EnvironmentalTransition)
    cold: EnvironmentalTransition = field(default_factory=EnvironmentalTransition)

    def as_dict(self) -> dict[str, object]:
        return {name: getattr(self, name).as_dict() for name in ("heat", "glare", "cold")}
