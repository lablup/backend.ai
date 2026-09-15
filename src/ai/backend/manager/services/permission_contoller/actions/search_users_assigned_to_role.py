from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher


@dataclass(frozen=True)
class GlobalSearchRoleAssignmentsAction(BaseGlobalAction):
    """Page through every role assignment, whichever user or role it joins."""

    searcher: RoleAssignmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_role_assignments"


@dataclass(frozen=True)
class GlobalSearchRoleAssignmentsActionResult:
    result: SearchResult[AssignedUserData]
