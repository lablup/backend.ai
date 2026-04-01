import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import (
    SessionSingleEntityAction,
    SessionSingleEntityActionResult,
)


# TODO: Change this to BatchAction since it can destroy multiple sessions with recursive option
@dataclass
class DestroySessionAction(SessionSingleEntityAction):
    user_role: UserRole
    session_name: str
    forced: bool
    recursive: bool
    owner_access_key: AccessKey
    session_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        # TODO: Handle this
        # if self.recursive:
        #     return "destroy_multi"
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION, str(self.session_id))


@dataclass
class DestroySessionActionResult(SessionSingleEntityActionResult):
    # TODO: Add proper type
    result: Any
    session_id: uuid.UUID

    # TODO: Change this to `entity_ids`
    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)
