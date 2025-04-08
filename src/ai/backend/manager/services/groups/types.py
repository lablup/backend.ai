import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Self, override

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState, TriStateEnum


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

    def get_creation_data(self) -> dict[str, Any]:
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
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("name"))
    domain_name: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("domain_name")
    )
    description: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("description")
    )
    is_active: OptionalState[bool] = field(default_factory=lambda: OptionalState.nop("is_active"))
    total_resource_slots: TriState[Optional[ResourceSlot]] = field(
        default_factory=lambda: TriState.nop("total_resource_slots")
    )
    allowed_vfolder_hosts: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    integration_id: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("integration_id")
    )
    resource_policy: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("resource_policy")
    )
    type: OptionalState[ProjectType] = field(default_factory=lambda: OptionalState.nop("type"))
    container_registry: OptionalState[dict[str, str]] = field(
        default_factory=lambda: OptionalState.nop("container_registry")
    )
    user_update_mode: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("user_update_mode")
    )
    user_uuids: OptionalState[List[str]] = field(
        default_factory=lambda: OptionalState.nop("user_uuids")
    )

    @override
    def get_modified_fields(self) -> dict[str, Any]:
        modified: dict[str, Any] = {}
        if self.name.state() != TriStateEnum.NOP:
            modified["name"] = self.name.value()
        if self.description.state() != TriStateEnum.NOP:
            modified["description"] = self.description.value()
        if self.is_active.state() != TriStateEnum.NOP:
            modified["is_active"] = self.is_active.value()
        if self.total_resource_slots.state() != TriStateEnum.NOP:
            modified["total_resource_slots"] = self.total_resource_slots.value()
        if self.allowed_vfolder_hosts.state() != TriStateEnum.NOP:
            modified["allowed_vfolder_hosts"] = self.allowed_vfolder_hosts.value()
        if self.integration_id.state() != TriStateEnum.NOP:
            modified["integration_id"] = self.integration_id.value()
        if self.resource_policy.state() != TriStateEnum.NOP:
            modified["resource_policy"] = self.resource_policy.value()
        if self.type.state() != TriStateEnum.NOP:
            modified["type"] = self.type.value()
        if self.container_registry.state() != TriStateEnum.NOP:
            modified["container_registry"] = self.container_registry.value()
        return modified
