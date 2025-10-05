from __future__ import annotations

import enum
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Self, override
from uuid import UUID

from sqlalchemy.engine import Row

from ai.backend.common.types import AccessKey, CIStrEnum
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.types import Creator

from ..keypair.types import KeyPairData

if TYPE_CHECKING:
    from ai.backend.manager.models.hasher.types import PasswordInfo


class UserStatus(enum.StrEnum):
    """
    User account status.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"

    @override
    @classmethod
    def _missing_(cls, value: Any) -> Optional[UserStatus]:
        assert isinstance(value, str)
        match value.upper():
            case "ACTIVE":
                return cls.ACTIVE
            case "INACTIVE":
                return cls.INACTIVE
            case "DELETED":
                return cls.DELETED
            case "BEFORE-VERIFICATION" | "BEFORE_VERIFICATION":
                return cls.BEFORE_VERIFICATION
        return None


class UserRole(CIStrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


@dataclass
class UserCreator(Creator):
    email: str
    username: str
    password: PasswordInfo  # Only accept PasswordInfo
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
    container_uid: Optional[int] = None
    container_main_gid: Optional[int] = None
    container_gids: Optional[list[int]] = None

    def fields_to_store(self) -> dict[str, Any]:
        status = UserStatus.ACTIVE  # TODO: Need to be set in action explicitly not in service (integrate is_active and status)
        if self.status is None and self.is_active is not None:
            status = UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE
        if self.status is not None:
            status = self.status
        user_data = {
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "need_password_change": self.need_password_change,
            "domain_name": self.domain_name,
            "full_name": self.full_name,
            "description": self.description,
            "status": status,
            "role": self.role,
            "allowed_client_ip": self.allowed_client_ip,
            "totp_activated": self.totp_activated,
            "resource_policy": self.resource_policy,
            "sudo_session_enabled": self.sudo_session_enabled,
            "container_uid": self.container_uid,
            "container_main_gid": self.container_main_gid,
            "container_gids": self.container_gids,
        }
        if self.container_uid is not None:
            user_data["container_uid"] = self.container_uid
        if self.container_main_gid is not None:
            user_data["container_main_gid"] = self.container_main_gid
        if self.container_gids is not None:
            user_data["container_gids"] = self.container_gids
        return user_data


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
    role: UserRole
    resource_policy: str
    allowed_client_ip: Optional[list[str]]
    totp_activated: bool
    totp_activated_at: Optional[datetime] = field(compare=False)
    sudo_session_enabled: bool
    main_access_key: Optional[str] = field(compare=False)
    container_uid: Optional[int] = field(compare=False)
    container_main_gid: Optional[int] = field(compare=False)
    container_gids: Optional[list[int]] = field(compare=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type=ScopeType.USER,
            scope_id=str(self.id),
        )

    def role_name(self) -> str:
        return f"user-{str(self.id)[:8]}"

    def entity_operations(self) -> Mapping[EntityType, Iterable[OperationType]]:
        resource_entity_permissions = {
            entity: OperationType.owner_operations()
            for entity in EntityType.owner_accessible_entity_types_in_user()
        }
        user_permissions = OperationType.owner_operations() - {OperationType.CREATE}
        return {EntityType.USER: user_permissions, **resource_entity_permissions}

    @classmethod
    def from_row(cls, row: Row) -> Self:
        """
        Deprecated: Use `UserRow.to_data()` method instead.
        """
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
class UserCreateResultData:
    user: UserData
    keypair: KeyPairData
