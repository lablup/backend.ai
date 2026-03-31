from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.group.types import UnassignUserFailure
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.group.scope_binders import UserProjectEntityUnbinder
from ai.backend.manager.services.group.actions.base import (
    GroupSingleEntityAction,
    GroupSingleEntityActionResult,
)


@dataclass
class UnassignUsersFromProjectAction(GroupSingleEntityAction):
    unbinder: UserProjectEntityUnbinder

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.unbinder.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.unbinder.project_id))


@dataclass
class UnassignUsersFromProjectActionResult(GroupSingleEntityActionResult):
    project_id: UUID
    unassigned_users: list[UserData] = field(default_factory=list)
    failures: list[UnassignUserFailure] = field(default_factory=list)

    @override
    def target_entity_id(self) -> str:
        return str(self.project_id)
