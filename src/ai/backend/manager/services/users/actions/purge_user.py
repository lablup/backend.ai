from dataclasses import dataclass
from typing import Optional

from ai.backend.common.types import Sentinel
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.users.actions.base import UserAction
from ai.backend.manager.services.users.type import UserInfoContext


@dataclass
class PurgeUserAction(UserAction):
    user_info_ctx: UserInfoContext
    email: str
    purge_shared_vfolders: bool | Sentinel = False
    delegate_endpoint_ownership: bool | Sentinel = False

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "purge"


@dataclass
class PurgeUserActionResult(BaseActionResult):
    success: bool

    def entity_id(self) -> Optional[str]:
        return None
