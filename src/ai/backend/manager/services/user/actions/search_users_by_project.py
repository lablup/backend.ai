from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.scopes import ProjectUserOperationScope
from ai.backend.manager.models.user.searchers import UserSearcher

__all__ = ("SearchUsersByProjectAction",)


@dataclass(frozen=True)
class SearchUsersByProjectAction(OperationScopeOpsAction[UserRow, UserData]):
    """Page through the users of a project."""

    project_id: ProjectID
    searcher: UserSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (ProjectUserOperationScope(project_id=self.project_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_users_by_project"

    @override
    def to_searcher(self) -> UserSearcher:
        return self.searcher
