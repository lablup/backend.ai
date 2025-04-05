from dataclasses import dataclass
from typing import Optional

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.users.actions.base import UserAction
from ai.backend.manager.services.users.type import UserData


@dataclass
class CreateUserAction(UserAction):
    username: str
    password: str
    email: str
    need_password_change: bool
    domain_name: str
    full_name: Optional[str]
    description: Optional[str]
    is_active: Optional[bool]
    status: Optional[UserStatus]
    role: Optional[UserRole]
    allowed_client_ip: Optional[str]
    totp_activated: Optional[bool]
    resource_policy: Optional[str]
    sudo_session_enabled: Optional[bool]
    group_ids: Optional[list[str]]
    container_uid: Optional[int]
    container_main_gid: Optional[int]
    container_gids: Optional[list[int]]

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
