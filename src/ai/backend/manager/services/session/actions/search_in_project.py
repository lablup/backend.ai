from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.session.types import ProjectSessionOperationScope
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


@dataclass
class SearchSessionsInProjectAction(SessionScopeAction):
    """Search sessions within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    scope: ProjectSessionOperationScope
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(self.scope.project_id)),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_sessions_in_project"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchSessionsInProjectActionResult(SessionScopeActionResult):
    data: list[SessionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
