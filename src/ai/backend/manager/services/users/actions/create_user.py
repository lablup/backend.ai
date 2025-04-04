from dataclasses import dataclass, field
from typing import Any, Optional, cast

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.users.actions.base import UserAction
from ai.backend.manager.services.users.type import UserData
from ai.backend.manager.types import OptionalState, State


@dataclass
class CreateUserAction(UserAction):
    username: str
    password: str
    email: str
    need_password_change: bool
    domain_name: str
    full_name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("full_name"))
    description: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    status: OptionalState[UserStatus] = field(default_factory=lambda: OptionalState.nop("status"))
    role: OptionalState[UserRole] = field(default_factory=lambda: OptionalState.nop("role"))
    allowed_client_ip: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_client_ip")
    )
    totp_activated: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("totp_activated")
    )
    resource_policy: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("resource_policy")
    )
    sudo_session_enabled: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("sudo_session_enabled")
    )
    group_ids: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("group_ids")
    )
    container_uid: OptionalState[Optional[int]] = field(
        default_factory=lambda: OptionalState.nop("container_uid")
    )
    container_main_gid: OptionalState[Optional[int]] = field(
        default_factory=lambda: OptionalState.nop("container_main_gid")
    )
    container_gids: OptionalState[Optional[list[int]]] = field(
        default_factory=lambda: OptionalState.nop("container_gids")
    )

    def __post_init__(self) -> None:
        if self.status.state() == State.NOP and self.is_active.state() == State.UPDATE:
            self.status = (
                OptionalState.update("status", UserStatus.ACTIVE)
                if self.is_active.value()
                else OptionalState.update("status", UserStatus.INACTIVE)
            )

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "create"

    def get_insertion_data(self) -> dict[str, Any]:
        username = self.username if self.username else self.email

        user_data = {
            "username": username,
            "email": self.email,
            "password": self.password,
            "need_password_change": self.need_password_change,
            "domain_name": self.domain_name,
            "status_info": "admin-requested",  # user mutation is only for admin
        }

        optional_fields = [
            "full_name",
            "description",
            "status",
            "role",
            "allowed_client_ip",
            "totp_activated",
            "resource_policy",
            "sudo_session_enabled",
            "container_uid",
            "container_main_gid",
            "container_gids",
        ]

        for field_name in optional_fields:
            field_value: OptionalState = getattr(self, field_name)
            if field_value.state() != State.NOP:
                user_data[field_name] = cast(Any, field_value.value())

        return user_data


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
