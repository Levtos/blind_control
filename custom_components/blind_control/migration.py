"""Pure, boundary-safe entity-reference migration helpers for AP3 runbooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ConsumerReference:
    """One inventoried consumer location without installation payload data."""

    surface: str
    locator: str
    mutable_during_cutover: bool = True


@dataclass(frozen=True, slots=True)
class RenameMigrationPlan:
    """Reversible exact-ID migration plan prepared before the live gate."""

    old_entity_id: str
    new_entity_id: str
    consumers: tuple[ConsumerReference, ...]

    def __post_init__(self) -> None:
        if not _is_cover_entity_id(self.old_entity_id):
            raise ValueError("old_entity_id must be a cover entity")
        if not _is_cover_entity_id(self.new_entity_id):
            raise ValueError("new_entity_id must be a cover entity")
        if self.old_entity_id == self.new_entity_id:
            raise ValueError("rename requires two different entity IDs")

    def migrate(self, value: Any) -> Any:
        """Replace exact references recursively without substring replacement."""

        return _replace_exact(value, self.old_entity_id, self.new_entity_id)

    def rollback(self, value: Any) -> Any:
        """Reverse the prepared replacement with the same exact-match rules."""

        return _replace_exact(value, self.new_entity_id, self.old_entity_id)

    def public_summary(self) -> dict[str, object]:
        """Return redacted inventory evidence suitable for Issue/PR output."""

        by_surface: dict[str, int] = {}
        for consumer in self.consumers:
            by_surface[consumer.surface] = by_surface.get(consumer.surface, 0) + 1
        return {
            "old_entity": "redacted_current_cover",
            "new_entity": "canonical_target_cover",
            "consumer_count": len(self.consumers),
            "consumers_by_surface": dict(sorted(by_surface.items())),
            "rollback_prepared": True,
        }


def _replace_exact(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return new if value == old else value
    if isinstance(value, list):
        return [_replace_exact(item, old, new) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_exact(item, old, new) for item in value)
    if isinstance(value, dict):
        return {
            (new if key == old else key): _replace_exact(item, old, new)
            for key, item in value.items()
        }
    return value


def _is_cover_entity_id(value: object) -> bool:
    return isinstance(value, str) and value.startswith("cover.") and len(value) > 6
