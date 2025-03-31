from dataclasses import dataclass
from typing import Any, Optional, override

import sqlalchemy as sa

from ai.backend.common.types import Sentinel
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.users.actions.base import UserAction
from ai.backend.manager.services.users.type import UserData


@dataclass
class ModifyUserAction(UserAction):
    email: str
    username: str | Sentinel = Sentinel.TOKEN
    password: str | Sentinel = Sentinel.TOKEN
    need_password_change: bool | Sentinel = Sentinel.TOKEN
    full_name: str | Sentinel = Sentinel.TOKEN
    description: str | Sentinel = Sentinel.TOKEN
    is_active: bool | Sentinel = Sentinel.TOKEN
    status: UserStatus | Sentinel = Sentinel.TOKEN
    domain_name: str | Sentinel = Sentinel.TOKEN
    role: UserRole | Sentinel = Sentinel.TOKEN
    group_ids: list[str] | Sentinel = Sentinel.TOKEN
    allowed_client_ip: Optional[list[str]] | Sentinel = Sentinel.TOKEN
    totp_activated: bool | Sentinel = False
    resource_policy: str | Sentinel = Sentinel.TOKEN
    sudo_session_enabled: bool | Sentinel = False
    main_access_key: Optional[str] | Sentinel = Sentinel.TOKEN
    container_uid: Optional[int] | Sentinel = Sentinel.TOKEN
    container_main_gid: Optional[int] | Sentinel = Sentinel.TOKEN
    container_gids: Optional[list[int]] | Sentinel = Sentinel.TOKEN

    @override
    def entity_id(self) -> Optional[str]:
        return self.username if self.username != Sentinel.TOKEN else None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_data(self) -> dict[str, Any]:
        sanitized_data = {k: v for k, v in self.__dict__.items() if v is not Sentinel.TOKEN}

        if hasattr(sanitized_data, "password") and sanitized_data["password"] is None:
            sanitized_data.pop("password", None)
        if hasattr(sanitized_data, "status") and sanitized_data["is_activate"] is None:
            sanitized_data["status"] = (
                UserStatus.ACTIVE if sanitized_data["is_active"] else UserStatus.INACTIVE
            )
        if hasattr(sanitized_data, "password") and sanitized_data["password"] is not None:
            sanitized_data["password_changed_at"] = sa.func.now()

        return sanitized_data

    @property
    def has_group_ids(self) -> bool:
        return (self.group_ids != Sentinel.TOKEN) and (self.group_ids is not None)


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
