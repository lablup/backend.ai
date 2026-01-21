from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
    granted_by: Optional[uuid.UUID]
    granted_at: datetime
    expires_at: Optional[datetime]
    deleted_at: Optional[datetime]


@dataclass
class UserRoleDataWithRole:
    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID]
    granted_at: datetime
    expires_at: Optional[datetime]
    deleted_at: Optional[datetime]

    mapped_role_data: RoleData
