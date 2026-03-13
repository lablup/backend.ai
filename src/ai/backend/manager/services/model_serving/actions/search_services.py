import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceSearchItem
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.types import QueryCondition
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceScopeAction,
    ModelServiceScopeActionResult,
)


@dataclass
class SearchServicesAction(ModelServiceScopeAction):
    session_owner_id: uuid.UUID
    _project_id: uuid.UUID
    conditions: list[QueryCondition] = field(default_factory=list)
    offset: int = 0
    limit: int = 20

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self._project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self._project_id))


@dataclass
class SearchServicesActionResult(ModelServiceScopeActionResult):
    items: list[ServiceSearchItem]
    total_count: int
    offset: int
    limit: int
    _project_id: uuid.UUID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self._project_id)
