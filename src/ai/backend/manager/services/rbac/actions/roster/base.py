from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction

__all__ = ("ProjectRosterAction",)


@dataclass(frozen=True)
class ProjectRosterAction(BaseScopeAction):
    """Base for an operation on a project's roster.

    One scope and one entity type: putting a user inside a project is a change to the
    project, so the permission asked is the ``user`` permission at that project
    (BEP-1076).
    """

    project_id: ProjectID
    user_ids: list[UserID]

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id)]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE
