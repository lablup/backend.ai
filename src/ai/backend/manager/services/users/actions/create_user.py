from dataclasses import dataclass, field
from typing import Any, Optional

from ai.backend.common.types import Sentinel
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
    full_name: str = ""
    description: str = ""
    is_active: Optional[bool] = True
    status: Optional[UserStatus] = UserStatus.ACTIVE
    domain_name: str = "default"
    role: UserRole = UserRole.USER
    allowed_client_ip: Optional[str] = None
    totp_activated: bool = False
    resource_policy: str = "default"
    sudo_session_enabled: bool = False
    group_ids: list[str] = field(default_factory=list)
    container_uid: Optional[int] | Sentinel = Sentinel.TOKEN
    container_main_gid: Optional[int] | Sentinel = Sentinel.TOKEN
    container_gids: Optional[list[int]] | Sentinel = Sentinel.TOKEN

    def __post_init__(self) -> None:
        if self.status is None and self.is_active is not None:
            self.status = UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE

    def entity_id(self) -> Optional[str]:
        return self.username

    def operation_type(self) -> str:
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        username = self.username if self.username else self.email
        if self.status is None and self.is_active is not None:
            self.status = UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE

        user_data = {
            "username": username,
            "email": self.email,
            "password": self.password,
            "need_password_change": self.need_password_change,
            "full_name": self.full_name,
            "description": self.description,
            "status": self.status,
            "status_info": "admin-requested",  # user mutation is only for admin
            "domain_name": self.domain_name,
            "role": self.role,
            "allowed_client_ip": self.allowed_client_ip,
            "totp_activated": self.totp_activated,
            "resource_policy": self.resource_policy,
            "sudo_session_enabled": self.sudo_session_enabled,
        }

        if self.container_uid is not Sentinel.TOKEN:
            user_data["container_uid"] = self.container_uid

        if self.container_main_gid is not Sentinel.TOKEN:
            user_data["container_main_gid"] = self.container_main_gid

        if self.container_gids is not Sentinel.TOKEN:
            user_data["container_gids"] = self.container_gids

        return user_data


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    def entity_id(self) -> Optional[str]:
        return self.data.username if self.data else None
