from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.user.types import UserInfoContext
from ai.backend.manager.services.user.actions.base import UserAction
from ai.backend.manager.types import OptionalState


@dataclass
class PurgeUserAction(UserAction):
    user_info_ctx: UserInfoContext
    email: str
    purge_shared_vfolders: OptionalState[bool] = field(default_factory=OptionalState.nop)
    delegate_endpoint_ownership: OptionalState[bool] = field(default_factory=OptionalState.nop)

    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "purge"


@dataclass
class PurgeUserActionResult(BaseActionResult):
    def entity_id(self) -> Optional[str]:
        return None
