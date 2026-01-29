from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from .role import RoleData


@dataclass
class UserRoleUpdateInput:
    pass


@dataclass
class UserRoleDeleteInput:
    id: uuid.UUID


@dataclass
class UserRoleData:
    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: uuid.UUID | None
    granted_at: datetime
    expires_at: datetime | None
    deleted_at: datetime | None


@dataclass
class UserRoleDataWithRole:
    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: uuid.UUID | None
    granted_at: datetime
    expires_at: datetime | None
    deleted_at: datetime | None

    mapped_role_data: RoleData
