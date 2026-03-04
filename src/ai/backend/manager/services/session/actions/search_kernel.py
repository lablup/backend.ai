from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.session.base import SessionScopeAction


@dataclass
class SearchKernelsAction(SessionScopeAction):
    """Search kernels within a scope (domain/project).

    RBAC validation checks if the user has READ permission in the target scope.
    """

    querier: BatchQuerier
    _scope_type: ScopeType = ScopeType.GLOBAL  # TODO: Set from context
    _scope_id: str = ""  # TODO: Set from context

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_KERNEL

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType(self._scope_type.value),
            element_id=self._scope_id,
        )


@dataclass
class SearchKernelsActionResult(BaseActionResult):
    data: list[KernelInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
