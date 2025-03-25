import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from sqlalchemy import Table

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType


@dataclass
class GroupData:
    id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    modified_at: datetime
    integration_id: Optional[str]
    domain_name: str
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: VFolderHostPermissionMap
    dotfiles: bytes
    resource_policy: str
    type: ProjectType
    container_registry: dict[str, str]

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

    @classmethod
    def from_table_var(cls, table_var: Optional[Table]) -> Optional[Self]:
        if table_var is None:
            return None
        return cls(
            id=table_var.c.id,
            name=table_var.c.name,
            description=table_var.c.description,
            is_active=table_var.c.is_active,
            created_at=table_var.c.created_at,
            modified_at=table_var.c.modified_at,
            integration_id=table_var.c.integration_id,
            domain_name=table_var.c.domain_name,
            total_resource_slots=table_var.c.total_resource_slots,
            allowed_vfolder_hosts=table_var.c.allowed_vfolder_hosts,
            dotfiles=table_var.c.dotfiles,
            resource_policy=table_var.c.resource_policy,
            type=table_var.c.type,
            container_registry=table_var.c.container_registry,
        )
