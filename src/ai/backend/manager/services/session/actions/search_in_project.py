from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.session.types import ProjectSessionSearchScope
from ai.backend.manager.services.session.base import SessionScopeAction


@dataclass
class SearchSessionsInProjectAction(SessionScopeAction):
    """Search sessions within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    scope: ProjectSessionSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.scope.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.PROJECT,
            element_id=str(self.scope.project_id),
        )


@dataclass
class SearchSessionsInProjectActionResult(BaseActionResult):
    data: list[SessionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
