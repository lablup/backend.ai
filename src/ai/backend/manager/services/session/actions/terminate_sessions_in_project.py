from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.session.base import SessionScopeAction


@dataclass
class TerminateSessionsInProjectAction(SessionScopeAction):
    """Terminate one or more sessions within a project scope.

    RBAC validation checks if the user has DELETE permission in PROJECT scope.
    Used for project admin page.
    """

    project_id: UUID
    session_ids: list[SessionId]
    forced: bool

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.PROJECT,
            element_id=str(self.project_id),
        )


@dataclass
class TerminateSessionsInProjectActionResult(BaseActionResult):
    """Result of project-scoped batch session termination."""

    cancelled: list[UUID] = field(default_factory=list)
    terminating: list[UUID] = field(default_factory=list)
    force_terminated: list[UUID] = field(default_factory=list)
    skipped: list[UUID] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
