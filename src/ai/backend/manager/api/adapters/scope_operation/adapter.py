"""Scope operation adapter answering where a scope operation may be targeted."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.scope_operation.response import (
    ListScopeOperationsPayload,
    ScopeOperationNode,
)
from ai.backend.manager.api.adapters.scope_operation.types import WiredScopeOperations


class ScopeOperationAdapter:
    """Adapter for reads over the scope operations themselves."""

    _scope_operations: WiredScopeOperations

    def __init__(self, scope_operations: WiredScopeOperations) -> None:
        self._scope_operations = scope_operations

    def list_scope_operations(self) -> ListScopeOperationsPayload:
        """Every operation the wiring targets by scope."""
        return ListScopeOperationsPayload(
            items=[
                ScopeOperationNode(
                    action_name=operation.action_name,
                    entity_type=str(operation.entity_type),
                    operation=str(operation.operation),
                    scope_types=[str(scope_type) for scope_type in operation.scope_types],
                )
                for operation in self._scope_operations.all()
            ]
        )


__all__ = ("ScopeOperationAdapter",)
