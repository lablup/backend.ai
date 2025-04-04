import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Self

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType


@dataclass
class GroupData:
    # TODO: If partial matching test is implemented, we need to remove 'id' from the ignore list
    id: uuid.UUID = field(compare=False)
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime = field(compare=False)
    modified_at: datetime = field(compare=False)
    integration_id: Optional[str]
    domain_name: str
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: VFolderHostPermissionMap
    dotfiles: bytes
    resource_policy: str
    type: ProjectType
    container_registry: Optional[dict[str, str]]

    @classmethod
    def from_row(cls, row: Optional[GroupRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            created_at=row.created_at,
            modified_at=row.modified_at,
            integration_id=row.integration_id,
            domain_name=row.domain_name,
            total_resource_slots=row.total_resource_slots,
            allowed_vfolder_hosts=row.allowed_vfolder_hosts,
            dotfiles=row.dotfiles,
            resource_policy=row.resource_policy,
            type=row.type,
            container_registry=row.container_registry,
        )
