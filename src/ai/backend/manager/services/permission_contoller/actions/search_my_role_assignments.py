from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.scopes import RoleAssignmentTarget
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "ScopedSearchRoleAssignmentsAction",
    "ScopedSearchRoleAssignmentsActionResult",
)


@dataclass(frozen=True)
class ScopedSearchRoleAssignmentsAction(BaseScopeAction):
    """Read the assignment rows the named scopes reach, combined with OR.

    The rows join a user to a role and belong to neither, so the read is answered for
    by the scopes it stays inside rather than by a row of its own.
    """

    targets: Sequence[RoleAssignmentTarget]
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
        return "scoped_search_role_assignments"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets


@dataclass(frozen=True)
class ScopedSearchRoleAssignmentsActionResult(BaseScopeActionResult):
    result: SearchResult[AssignedUserData]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return []
