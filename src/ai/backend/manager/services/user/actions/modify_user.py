from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.user.actions.base import UserAction
from ai.backend.manager.services.user.type import UserData
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class UserModifier(PartialModifier):
    username: OptionalState[str] = field(default_factory=OptionalState.nop)
    password: OptionalState[str] = field(default_factory=OptionalState.nop)
    need_password_change: OptionalState[bool] = field(default_factory=OptionalState.nop)
    full_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    description: OptionalState[str] = field(default_factory=OptionalState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    status: OptionalState[UserStatus] = field(default_factory=OptionalState.nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    role: OptionalState[UserRole] = field(default_factory=OptionalState.nop)
    allowed_client_ip: TriState[list[str]] = field(default_factory=TriState.nop)
    totp_activated: OptionalState[bool] = field(default_factory=OptionalState.nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState.nop)
    sudo_session_enabled: OptionalState[bool] = field(default_factory=OptionalState.nop)
    main_access_key: TriState[str] = field(default_factory=TriState.nop)
    container_uid: TriState[int] = field(default_factory=TriState.nop)
    container_main_gid: TriState[int] = field(default_factory=TriState.nop)
    container_gids: TriState[list[int]] = field(default_factory=TriState.nop)

    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.need_password_change.update_dict(to_update, "need_password_change")
        self.full_name.update_dict(to_update, "full_name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.status.update_dict(to_update, "status")
        self.domain_name.update_dict(to_update, "domain_name")
        self.role.update_dict(to_update, "role")
        self.allowed_client_ip.update_dict(to_update, "allowed_client_ip")
        self.totp_activated.update_dict(to_update, "totp_activated")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.sudo_session_enabled.update_dict(to_update, "sudo_session_enabled")
        self.container_uid.update_dict(to_update, "container_uid")
        self.container_main_gid.update_dict(to_update, "container_main_gid")
        self.container_gids.update_dict(to_update, "container_gids")
        return to_update


@dataclass
class ModifyUserAction(UserAction):
    email: str
    modifier: UserModifier
    group_ids: OptionalState[list[str]] = field(default_factory=OptionalState.nop)

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: Optional[UserData]
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data else None
