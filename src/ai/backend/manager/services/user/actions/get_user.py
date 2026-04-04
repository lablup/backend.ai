from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.user.actions.base import (
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)


@dataclass
class GetUserAction(UserSingleEntityAction):
    """Action to retrieve a single user by UUID."""

    user_uuid: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_uuid))


@dataclass
class GetUserActionResult(UserSingleEntityActionResult):
    """Result of GetUserAction containing user data."""

    user: UserData

    @override
    def entity_id(self) -> str | None:
        return str(self.user.uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.user.uuid)
