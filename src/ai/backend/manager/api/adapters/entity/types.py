"""The entity types a request may name."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.errors.api import InvalidAPIParameters


class WiredEntityTypes:
    """Every entity type the processor wiring names, read once at startup.

    An entity type is declared where its operations are wired rather than in an enum,
    so what a caller may name is whatever the wiring covers. `global` is wiring only
    and names no entity, so it is left out.
    """

    _types: frozenset[EntityType]
    _sorted: tuple[EntityType, ...]

    def __init__(self, registry: ProcessorRegistry[Any]) -> None:
        self._types = frozenset(
            wiring.entity_type
            for wiring in registry.wired_processors()
            if wiring.entity_type != GLOBAL_ENTITY_TYPE
        )
        self._sorted = tuple(sorted(self._types))

    def all(self) -> Sequence[EntityType]:
        """Every entity type, in name order."""
        return self._sorted

    def resolve(self, name: str) -> EntityType:
        """The entity type the name stands for; an unwired name is refused here."""
        entity_type = EntityType(name)
        if entity_type not in self._types:
            raise InvalidAPIParameters(f"{name!r} is not an entity type")
        return entity_type
