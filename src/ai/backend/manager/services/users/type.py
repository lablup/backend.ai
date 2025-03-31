import logging
import uuid
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional, Self

from sqlalchemy.engine import Row

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.user import UserStatus


@dataclass
class UserInfoContext:
    uuid: uuid.UUID
    email: str
    main_access_key: AccessKey


@dataclass
class UserData:
    id: uuid.UUID
    uuid: uuid.UUID  # legacy
    username: str
    email: str
    need_password_change: bool
    full_name: str
    description: str
    is_active: bool  # legacy
    status: str
    status_info: Optional[str]
    created_at: datetime
    modified_at: datetime
    domain_name: str
    role: str
    resource_policy: str
    allowed_client_ip: Optional[list[str]]
    totp_activated: bool
    totp_activated_at: Optional[datetime]
    sudo_session_enabled: bool
    main_access_key: Optional[str]
    container_uid: Optional[int]
    container_main_gid: Optional[int]
    container_gids: Optional[list[int]]

    def __eq__(self, other):
        if not isinstance(other, UserData):
            return False

        ignore_fields = [
            "id",
            "uuid",
            "created_at",
            "modified_at",
            "totp_activated_at",
            "main_access_key",
            "container_uid",
            "container_main_gid",
            "container_gids",
        ]

        for field in fields(self):
            if field.name not in ignore_fields:
                if getattr(self, field.name) != getattr(other, field.name):
                    logging.error(
                        f"Field {field.name} does not match: {getattr(self, field.name)} != {getattr(other, field.name)}"
                    )
                    return False
        return True

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
