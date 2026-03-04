from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionSingleEntityAction


# TODO: Change this to BatchAction since it can destroy multiple sessions with recursive option
@dataclass
class DestroySessionAction(SessionSingleEntityAction):
    """Destroy a specific session.

    RBAC validation checks if the user has DELETE permission for this session.
    session_id must be resolved from session_name before RBAC validation.
    """

    user_role: UserRole
    session_name: str
    forced: bool
    recursive: bool
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return self.session_id if self.session_id else None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        # TODO: Handle this
        # if self.recursive:
        #     return "destroy_multi"
        return ActionOperationType.DELETE


@dataclass
class DestroySessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any

    # TODO: Change this to `entity_ids`
    @override
    def entity_id(self) -> str | None:
        return None
