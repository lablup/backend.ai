"""The operations the wiring targets by scope."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction


@dataclass(frozen=True)
class WiredScopeOperation:
    """One wired scope operation, addressed by its entity type and its name."""

    action_name: str
    entity_type: EntityType
    operation: ActionOperationType
    scope_types: tuple[EntityType, ...]


class WiredScopeOperations:
    """Every operation the processor wiring targets by scope, read once at startup.

    Which scope types an operation accepts is the action's own declaration, so this
    cannot drift from what the wiring dispatches.
    """

    _operations: tuple[WiredScopeOperation, ...]

    def __init__(self, registry: ProcessorRegistry[Any]) -> None:
        self._operations = tuple(
            sorted(
                (
                    WiredScopeOperation(
                        action_name=wiring.action_cls.action_name(),
                        entity_type=wiring.entity_type,
                        operation=wiring.action_cls.operation_type(),
                        scope_types=tuple(wiring.action_cls.available_scope_types()),
                    )
                    for wiring in registry.wired_processors()
                    if issubclass(wiring.action_cls, BaseScopeAction)
                ),
                key=lambda operation: (
                    operation.entity_type,
                    operation.action_name,
                    operation.operation,
                ),
            )
        )

    def all(self) -> Sequence[WiredScopeOperation]:
        """Every scope operation, in entity type then name order."""
        return self._operations
