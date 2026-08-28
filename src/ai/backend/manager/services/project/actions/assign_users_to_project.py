from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.project.types import AssignUserFailure
from ai.backend.manager.data.user.types import UserData


@dataclass(frozen=True)
class AssignUsersToProjectAction(BaseSingleEntityAction):
    """Enroll users in a project. Membership is a change to the project."""

    project_id: ProjectID
    user_ids: list[UUID]
    role_id: UUID

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
        return "assign_users_to_project"


@dataclass(frozen=True)
class AssignUsersToProjectActionResult:
    project_id: ProjectID
    assigned_users: list[UserData]
    failures: list[AssignUserFailure]
