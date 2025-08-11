from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
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
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        # TODO: Handle this
        # if self.recursive:
        #     return "destory_multi"
        return "destory"


@dataclass
class DestroySessionActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any

    # TODO: Change this to `entity_ids`
    @override
    def entity_id(self) -> Optional[str]:
        return None
