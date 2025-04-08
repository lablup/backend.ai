import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self, override

from sqlalchemy.engine.result import Row

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.types import Creator


@dataclass
class UserInfo:
    id: uuid.UUID
    role: UserRole
    domain_name: str


@dataclass
class DomainData:
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime = field(compare=False)
    modified_at: datetime = field(compare=False)
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: VFolderHostPermissionMap
    allowed_docker_registries: list[str]
    dotfiles: bytes
    integration_id: Optional[str]

    @classmethod
    def from_row(cls, row: Optional[DomainRow | Row]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            total_resource_slots=row.total_resource_slots,
            allowed_vfolder_hosts=row.allowed_vfolder_hosts,
            allowed_docker_registries=row.allowed_docker_registries,
            dotfiles=row.dotfiles,
            integration_id=row.integration_id,
        )


@dataclass
class DomainCreator(Creator):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = None
    total_resource_slots: Optional[ResourceSlot] = None
    allowed_vfolder_hosts: Optional[dict[str, str]] = None
    allowed_docker_registries: Optional[list[str]] = None
    integration_id: Optional[str] = None
    dotfiles: Optional[bytes] = None

    @override
    def get_creation_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "allowed_docker_registries": self.allowed_docker_registries,
            "integration_id": self.integration_id,
            "dotfiles": self.dotfiles,
        }


@dataclass
class DomainNodeCreator(DomainCreator):
    scaling_groups: Optional[list[str]] = None

    def get_creation_data(self) -> dict[str, Any]:
        data = super().get_creation_data()
        data["scaling_groups"] = self.scaling_groups
        return data
