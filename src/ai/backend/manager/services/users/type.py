from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self, override
from uuid import UUID

from sqlalchemy.engine import Row

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


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

    def fields_to_store(self) -> dict[str, Any]:
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
    username: OptionalState[str] = field(
        default_factory=OptionalState.nop,
    )
    password: OptionalState[str] = field(default_factory=OptionalState.nop)
    need_password_change: OptionalState[bool] = field(
        default_factory=OptionalState.nop,
    )
    full_name: TriState[str] = field(default_factory=TriState.nop)
    description: TriState[str] = field(default_factory=TriState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    status: OptionalState[UserStatus] = field(default_factory=OptionalState.nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    role: OptionalState[UserRole] = field(default_factory=OptionalState.nop)
    allowed_client_ip: TriState[list[str]] = field(default_factory=TriState.nop)
    totp_activated: OptionalState[bool] = field(default_factory=OptionalState.nop)
    resource_policy: TriState[str] = field(default_factory=TriState.nop)
    sudo_session_enabled: OptionalState[bool] = field(default_factory=OptionalState.nop)
    container_uid: TriState[int] = field(default_factory=TriState.nop)
    container_main_gid: TriState[int] = field(default_factory=TriState.nop)
    container_gids: TriState[list[int]] = field(default_factory=TriState.nop)
    main_access_key: TriState[str] = field(default_factory=TriState.nop)
    group_ids: OptionalState[list[str]] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        modified: dict[str, Any] = {}
        self.username.update_dict(modified, "username")
        self.password.update_dict(modified, "password")
        self.need_password_change.update_dict(modified, "need_password_change")
        self.full_name.update_dict(modified, "full_name")
        self.description.update_dict(modified, "description")
        self.is_active.update_dict(modified, "is_active")
        self.status.update_dict(modified, "status")
        self.domain_name.update_dict(modified, "domain_name")
        self.role.update_dict(modified, "role")
        self.allowed_client_ip.update_dict(modified, "allowed_client_ip")
        self.totp_activated.update_dict(modified, "totp_activated")
        self.resource_policy.update_dict(modified, "resource_policy")
        self.sudo_session_enabled.update_dict(modified, "sudo_session_enabled")
        self.container_uid.update_dict(modified, "container_uid")
        self.container_main_gid.update_dict(modified, "container_main_gid")
        self.container_gids.update_dict(modified, "container_gids")
        self.main_access_key.update_dict(modified, "main_access_key")
        self.group_ids.update_dict(modified, "group_ids")
        return modified
