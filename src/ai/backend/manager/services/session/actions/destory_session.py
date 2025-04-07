from dataclasses import dataclass
from typing import Any, Iterable, Optional, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.session import SessionRow
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
    def operation_type(self):
        if self.recursive:
            return "destory_multi"
        return "destory"


@dataclass
class DestroySessionActionResult(BaseActionResult):
    destroyed_sessions: Iterable[SessionRow | BaseException]

    # TODO: Add proper type
    result: Any

    # TODO: Change this to `entity_ids`
    @override
    def entity_id(self) -> Optional[str]:
        return None
