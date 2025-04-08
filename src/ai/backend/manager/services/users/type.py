from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Self, override
from uuid import UUID

from sqlalchemy.engine import Row

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState, TriStateEnum


@dataclass
class UserCreator(Creator):
    email: str
    username: str
    password: str
    need_password_change: bool
    domain_name: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None
    role: Optional[str] = None
    allowed_client_ip: Optional[list[str]] = None
    totp_activated: Optional[bool] = None
    resource_policy: Optional[str] = None
    sudo_session_enabled: Optional[bool] = None
    group_ids: Optional[list[str]] = None
    container_uid: Optional[int] = None
    container_main_gid: Optional[int] = None
    container_gids: Optional[list[int]] = None

    def get_creation_data(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "need_password_change": self.need_password_change,
            "domain_name": self.domain_name,
            "full_name": self.full_name,
            "description": self.description,
            "is_active": self.is_active,
            "status": self.status,
            "role": self.role,
            "allowed_client_ip": self.allowed_client_ip,
            "totp_activated": self.totp_activated,
            "resource_policy": self.resource_policy,
            "sudo_session_enabled": self.sudo_session_enabled,
            "group_ids": self.group_ids,
            "container_uid": self.container_uid,
            "container_main_gid": self.container_main_gid,
            "container_gids": self.container_gids,
        }


@dataclass
class UserInfoContext:
    uuid: UUID
    email: str
    main_access_key: AccessKey


@dataclass
class UserData:
    id: UUID = field(compare=False)
    uuid: UUID = field(compare=False)  # legacy
    username: str
    email: str
    need_password_change: bool
    full_name: Optional[str]
    description: Optional[str]
    is_active: bool  # legacy
    status: str
    status_info: Optional[str]
    created_at: datetime = field(compare=False)
    modified_at: datetime = field(compare=False)
    domain_name: str
    role: str
    resource_policy: str
    allowed_client_ip: Optional[list[str]]
    totp_activated: bool
    totp_activated_at: Optional[datetime] = field(compare=False)
    sudo_session_enabled: bool
    main_access_key: Optional[str] = field(compare=False)
    container_uid: Optional[int] = field(compare=False)
    container_main_gid: Optional[int] = field(compare=False)
    container_gids: Optional[list[int]] = field(compare=False)

    @classmethod
    def from_row(cls, row: Row) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.uuid,
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            need_password_change=row.need_password_change,
            full_name=row.full_name,
            description=row.description,
            is_active=True if row.status == UserStatus.ACTIVE else False,
            status=row.status,
            status_info=row.status_info,
            created_at=row.created_at,
            modified_at=row.modified_at,
            domain_name=row.domain_name,
            role=row.role,
            resource_policy=row.resource_policy,
            allowed_client_ip=row.allowed_client_ip,
            totp_activated=row.totp_activated,
            totp_activated_at=row.totp_activated_at,
            sudo_session_enabled=row.sudo_session_enabled,
            main_access_key=row.main_access_key,
            container_uid=row.container_uid,
            container_main_gid=row.container_main_gid,
            container_gids=row.container_gids,
        )


@dataclass
class UserModifier(PartialModifier):
    username: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("username"))
    password: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("password"))
    need_password_change: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("need_password_change")
    )
    full_name: TriState[Optional[str]] = field(default_factory=lambda: TriState.nop("full_name"))
    description: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    status: OptionalState[UserStatus] = field(default_factory=lambda: OptionalState.nop("status"))
    domain_name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("domain_name")
    )
    role: OptionalState[UserRole] = field(default_factory=lambda: OptionalState.nop("role"))
    allowed_client_ip: TriState[Optional[List[str]]] = field(
        default_factory=lambda: TriState.nop("allowed_client_ip")
    )
    totp_activated: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("totp_activated")
    )
    resource_policy: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("resource_policy")
    )
    sudo_session_enabled: OptionalState[bool] = field(
        default_factory=lambda: OptionalState.nop("sudo_session_enabled")
    )
    container_uid: TriState[Optional[int]] = field(
        default_factory=lambda: TriState.nop("container_uid")
    )
    container_main_gid: TriState[Optional[int]] = field(
        default_factory=lambda: TriState.nop("container_main_gid")
    )
    container_gids: TriState[Optional[List[int]]] = field(
        default_factory=lambda: TriState.nop("container_gids")
    )
    main_access_key: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("main_access_key")
    )
    group_ids: OptionalState[List[str]] = field(
        default_factory=lambda: OptionalState.nop("group_ids")
    )

    @override
    def get_modified_fields(self) -> dict[str, Any]:
        modified: dict[str, Any] = {}
        if self.username.state() != TriStateEnum.NOP:
            modified["username"] = self.username.value()
        if self.password.state() != TriStateEnum.NOP:
            modified["password"] = self.password.value()
        if self.need_password_change.state() != TriStateEnum.NOP:
            modified["need_password_change"] = self.need_password_change.value()
        if self.full_name.state() != TriStateEnum.NOP:
            modified["full_name"] = self.full_name.value()
        if self.description.state() != TriStateEnum.NOP:
            modified["description"] = self.description.value()
        if self.is_active.state() != TriStateEnum.NOP:
            modified["is_active"] = self.is_active.value()
        if self.status.state() != TriStateEnum.NOP:
            modified["status"] = self.status.value()
        if self.domain_name.state() != TriStateEnum.NOP:
            modified["domain_name"] = self.domain_name.value()
        if self.role.state() != TriStateEnum.NOP:
            modified["role"] = self.role.value()
        if self.allowed_client_ip.state() != TriStateEnum.NOP:
            modified["allowed_client_ip"] = self.allowed_client_ip.value()
        if self.totp_activated.state() != TriStateEnum.NOP:
            modified["totp_activated"] = self.totp_activated.value()
        if self.resource_policy.state() != TriStateEnum.NOP:
            modified["resource_policy"] = self.resource_policy.value()
        if self.sudo_session_enabled.state() != TriStateEnum.NOP:
            modified["sudo_session_enabled"] = self.sudo_session_enabled.value()
        if self.container_uid.state() != TriStateEnum.NOP:
            modified["container_uid"] = self.container_uid.value()
        if self.container_main_gid.state() != TriStateEnum.NOP:
            modified["container_main_gid"] = self.container_main_gid.value()
        if self.container_gids.state() != TriStateEnum.NOP:
            modified["container_gids"] = self.container_gids.value()
        if self.main_access_key.state() != TriStateEnum.NOP:
            modified["main_access_key"] = self.main_access_key.value()
        return modified
