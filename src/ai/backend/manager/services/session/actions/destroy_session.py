from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.types import AccessKey, SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction


# TODO: Change this to BatchAction since it can destroy multiple sessions with recursive option
@dataclass
class DestroySessionAction(SessionAction):
    user_role: UserRole
    session_name: str
    forced: bool
    recursive: bool
    owner_access_key: AccessKey

    @override
    def entity_id(self) -> str | None:
        return None

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
    session_ids: list[SessionId] = field(default_factory=list)

    # TODO: Change this to `entity_ids` once BaseActionResultMeta supports
    # multiple ids; until then, comma-join so audit logs capture every
    # affected session (recursive destroy can target several).
    @override
    def entity_id(self) -> str | None:
        if not self.session_ids:
            return None
        return ",".join(str(sid) for sid in self.session_ids)
