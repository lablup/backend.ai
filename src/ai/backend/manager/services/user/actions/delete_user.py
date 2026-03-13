from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.user.actions.base import (
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)


@dataclass
class DeleteUserAction(UserSingleEntityAction):
    user_uuid: UUID
    email: str  # Still needed for the service layer implementation

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_uuid))


@dataclass
class DeleteUserActionResult(UserSingleEntityActionResult):
    user_uuid: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.user_uuid)
