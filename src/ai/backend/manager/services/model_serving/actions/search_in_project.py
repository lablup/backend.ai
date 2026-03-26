from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceSearchItem
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.model_serving.actions.base import ModelServiceScopeAction


@dataclass
class SearchServicesInProjectAction(ModelServiceScopeAction):
    """Search model serving services within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    querier: BatchQuerier
    project_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project_id))


@dataclass
class SearchServicesInProjectActionResult(BaseActionResult):
    items: list[ServiceSearchItem]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
