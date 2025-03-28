import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from sqlalchemy.engine import Row


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
    status_info: str
    created_at: datetime
    modified_at: datetime
    domain_name: str
    role: str
    resource_policy: str
    allowed_client_ip: list[str]
    totp_activated: bool
    totp_activated_at: datetime
    sudo_session_enabled: bool
    main_access_key: str
    container_uid: int
    container_main_gid: int
    container_gids: list[int]

    @classmethod
    def from_row(cls, row: Row) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            uuid=row.uuid,
            username=row.username,
            email=row.email,
            need_password_change=row.need_password_change,
            full_name=row.full_name,
            description=row.description,
            is_active=row.is_active,
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
