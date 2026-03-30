from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.group.actions.base import (
    GroupSingleEntityAction,
    GroupSingleEntityActionResult,
)


@dataclass
class AssignUsersToProjectAction(GroupSingleEntityAction):
    project_id: UUID
    user_ids: list[UUID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project_id))


@dataclass
class AssignUsersToProjectActionResult(GroupSingleEntityActionResult):
    project_id: UUID
    assigned_users: list[UserData]

    @override
    def target_entity_id(self) -> str:
        return str(self.project_id)
