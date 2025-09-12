import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.manager.types import Creator

from .role import RoleData


@dataclass
class UserRoleCreateInput(Creator):
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        data = {
            "user_id": self.user_id,
            "role_id": self.role_id,
        }
        if self.granted_by is not None:
            data["granted_by"] = self.granted_by
        return data


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
