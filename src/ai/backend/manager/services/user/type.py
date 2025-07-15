from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self
from uuid import UUID

from sqlalchemy.engine import Row

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserStatus
from ai.backend.manager.types import Creator


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
        fields = {
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "need_password_change": self.need_password_change,
            "domain_name": self.domain_name,
            "status_info": "admin-requested",  # user mutation is only for admin
        }

        # Optional fields
        if self.full_name is not None:
            fields["full_name"] = self.full_name
        if self.description is not None:
            fields["description"] = self.description
        if self.status is not None:
            fields["status"] = self.status
        if self.role is not None:
            fields["role"] = self.role
        if self.allowed_client_ip is not None:
            fields["allowed_client_ip"] = self.allowed_client_ip
        if self.totp_activated is not None:
            fields["totp_activated"] = self.totp_activated
        if self.resource_policy is not None:
            fields["resource_policy"] = self.resource_policy
        if self.sudo_session_enabled is not None:
            fields["sudo_session_enabled"] = self.sudo_session_enabled
        if self.container_uid is not None:
            fields["container_uid"] = self.container_uid
        if self.container_main_gid is not None:
            fields["container_main_gid"] = self.container_main_gid
        if self.container_gids is not None:
            fields["container_gids"] = self.container_gids

        # Note: is_active and group_ids are handled separately
        # is_active is converted to status in the service layer
        # group_ids are handled through separate association table

        return fields


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
