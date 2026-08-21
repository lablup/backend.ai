from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.group.types import UnassignUserFailure
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.group.scope_binders import UserProjectEntityUnbinder


@dataclass(frozen=True)
class UnassignUsersFromProjectAction(BaseSingleEntityAction):
    """Remove users from a project."""

    project_id: ProjectID
    unbinder: UserProjectEntityUnbinder

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "unassign_users_from_project"


@dataclass(frozen=True)
class UnassignUsersFromProjectActionResult:
    project_id: ProjectID
    unassigned_users: list[UserData] = field(default_factory=list)
    failures: list[UnassignUserFailure] = field(default_factory=list)
