"""The entity types a request may name."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.errors.api import InvalidAPIParameters


class WiredEntityTypes:
    """Every entity type the processor wiring names, read once at startup.

    An entity type is declared where its operations are wired rather than in an enum,
    so what a caller may name is whatever the wiring covers. `global` is wiring only
    and names no entity, so it is left out.
    """

    _types: frozenset[EntityType]
    _sorted: tuple[EntityType, ...]
    _scope_types: Mapping[EntityType, tuple[EntityType, ...]]

    def __init__(self, registry: ProcessorRegistry[Any]) -> None:
        self._types = frozenset(
            wiring.entity_type
            for wiring in registry.wired_processors()
            if wiring.entity_type != GLOBAL_ENTITY_TYPE
        )
        self._sorted = tuple(sorted(self._types))
        declared: dict[EntityType, set[EntityType]] = defaultdict(set)
        for wiring in registry.wired_processors():
            if wiring.entity_type in self._types and issubclass(wiring.action_cls, BaseScopeAction):
                declared[wiring.entity_type].update(wiring.action_cls.available_scope_types())
        self._scope_types = {
            entity_type: tuple(sorted(scope_types)) for entity_type, scope_types in declared.items()
        }

    def all(self) -> Sequence[EntityType]:
        """Every entity type, in name order."""
        return self._sorted

    def scope_types(self, entity_type: EntityType) -> Sequence[EntityType]:
        """The scope types an operation on this entity type may be targeted at.

        The union of what its scope actions declare, so an entity type no operation
        scopes has none. A read whose wiring fixes no owner is named by `global` and
        is not one of these.
        """
        return self._scope_types.get(entity_type, ())

    def resolve(self, name: str) -> EntityType:
        """The entity type the name stands for; an unwired name is refused here."""
        entity_type = EntityType(name)
        if entity_type not in self._types:
            raise InvalidAPIParameters(f"{name!r} is not an entity type")
        return entity_type
