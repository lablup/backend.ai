from dataclasses import dataclass, field, fields
from typing import Any, Optional, cast, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.users.actions.base import UserAction
from ai.backend.manager.services.users.type import UserData
from ai.backend.manager.types import OptionalState, TriStateEnum


@dataclass
class UserModifiableFields:
    username: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("username"))
    password: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("password"))
    need_password_change: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("need_password_change")
    )
    full_name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("full_name"))
    description: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    status: OptionalState[UserStatus] = field(default_factory=lambda: OptionalState.nop("status"))
    domain_name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("domain_name")
    )
    role: OptionalState[UserRole] = field(default_factory=lambda: OptionalState.nop("role"))
    group_ids: OptionalState[Optional[list[str]]] = field(
        default_factory=lambda: OptionalState.nop("group_ids")
    )
    allowed_client_ip: OptionalState[Optional[list[str]]] = field(
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
    main_access_key: OptionalState[Optional[str]] = field(
        default_factory=lambda: OptionalState.nop("main_access_key")
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

    def get_updated_fields(self) -> dict[str, Any]:
        result = {}
        for f in fields(self):
            field_value: OptionalState = getattr(self, f.name)
            if field_value.state() != TriStateEnum.NOP:
                result[f.name] = cast(Any, field_value.value())
        return result


@dataclass
class ModifyUserAction(UserAction):
    email: str
    modifiable_fields: UserModifiableFields

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_updated_fields(self) -> dict[str, Any]:
        return self.modifiable_fields.get_updated_fields()


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
