"""
Data types for group service.
Deprecated: use `ai.backend.manager.data.group.types` instead.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self, override

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


@dataclass
class GroupCreator(Creator):
    name: str
    domain_name: str
    type: Optional[ProjectType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    total_resource_slots: Optional[ResourceSlot] = None
    allowed_vfolder_hosts: Optional[dict[str, str]] = None
    integration_id: Optional[str] = None
    resource_policy: Optional[str] = None
    container_registry: Optional[dict[str, str]] = None
    dotfiles: Optional[bytes] = None

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain_name": self.domain_name,
            "type": self.type,
            "description": self.description,
            "is_active": self.is_active,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "integration_id": self.integration_id,
            "resource_policy": self.resource_policy,
            "container_registry": self.container_registry,
            "dotfiles": self.dotfiles,
        }


@dataclass
class GroupData:
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


@dataclass
class GroupModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(
        default_factory=TriState[str].nop,
    )
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    domain_name: OptionalState[str] = field(
        default_factory=OptionalState[str].nop,
    )
    total_resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=OptionalState[dict[str, str]].nop
    )
    integration_id: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    container_registry: TriState[dict[str, str]] = field(
        default_factory=TriState[dict[str, str]].nop
    )

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.domain_name.update_dict(to_update, "domain_name")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.integration_id.update_dict(to_update, "integration_id")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.container_registry.update_dict(to_update, "container_registry")
        return to_update
