import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self, override

from sqlalchemy.engine.result import Row

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, State, TriState


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


@dataclass
class DomainModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("name"))
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
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_docker_registries")
    )
    integration_id: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("integration_id")
    )

    @override
    def get_modified_fields(self) -> dict[str, Any]:
        modified: dict[str, Any] = {}
        if self.name.state() != State.NOP:
            modified["name"] = self.name.value()
        if self.description.state() != State.NOP:
            modified["description"] = self.description.value()
        if self.is_active.state() != State.NOP:
            modified["is_active"] = self.is_active.value()
        if self.total_resource_slots.state() != State.NOP:
            modified["total_resource_slots"] = self.total_resource_slots.value()
        if self.allowed_vfolder_hosts.state() != State.NOP:
            modified["allowed_vfolder_hosts"] = self.allowed_vfolder_hosts.value()
        if self.allowed_docker_registries.state() != State.NOP:
            modified["allowed_docker_registries"] = self.allowed_docker_registries.value()
        if self.integration_id.state() != State.NOP:
            modified["integration_id"] = self.integration_id.value()
        return modified


@dataclass
class DomainNodeModifier(PartialModifier):
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
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=lambda: OptionalState.nop("allowed_docker_registries")
    )
    integration_id: TriState[Optional[str]] = field(
        default_factory=lambda: TriState.nop("integration_id")
    )
    dotfiles: OptionalState[bytes] = field(default_factory=lambda: OptionalState.nop("dotfiles"))

    @override
    def get_modified_fields(self) -> dict[str, Any]:
        modified: dict[str, Any] = {}
        if self.description.state() != State.NOP:
            modified["description"] = self.description.value()
        if self.is_active.state() != State.NOP:
            modified["is_active"] = self.is_active.value()
        if self.total_resource_slots.state() != State.NOP:
            modified["total_resource_slots"] = self.total_resource_slots.value()
        if self.allowed_vfolder_hosts.state() != State.NOP:
            modified["allowed_vfolder_hosts"] = self.allowed_vfolder_hosts.value()
        if self.allowed_docker_registries.state() != State.NOP:
            modified["allowed_docker_registries"] = self.allowed_docker_registries.value()
        if self.integration_id.state() != State.NOP:
            modified["integration_id"] = self.integration_id.value()
        if self.dotfiles.state() != State.NOP:
            modified["dotfiles"] = self.dotfiles.value()
        return modified
