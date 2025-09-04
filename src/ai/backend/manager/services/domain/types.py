"""
Data types for domain service.
Deprecated: use `ai.backend.manager.data.domain.types` instead.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self, override

from sqlalchemy.engine.result import Row

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


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
    allowed_vfolder_hosts: Optional[dict[str, list[str]]] = None
    allowed_docker_registries: Optional[list[str]] = None
    integration_id: Optional[str] = None
    dotfiles: Optional[bytes] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            to_store["description"] = self.description
        if self.is_active is not None:
            to_store["is_active"] = self.is_active
        if self.total_resource_slots is not None:
            to_store["total_resource_slots"] = self.total_resource_slots
        if self.allowed_vfolder_hosts is not None:
            to_store["allowed_vfolder_hosts"] = self.allowed_vfolder_hosts
        if self.allowed_docker_registries is not None:
            to_store["allowed_docker_registries"] = self.allowed_docker_registries
        if self.integration_id is not None:
            to_store["integration_id"] = self.integration_id
        if self.dotfiles is not None:
            to_store["dotfiles"] = self.dotfiles
        return to_store


@dataclass
class DomainModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    description: TriState[str] = field(default_factory=TriState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    total_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState.nop)
    allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = field(
        default_factory=OptionalState.nop
    )
    allowed_docker_registries: OptionalState[list[str]] = field(default_factory=OptionalState.nop)
    integration_id: TriState[str] = field(default_factory=TriState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        self.integration_id.update_dict(to_update, "integration_id")
        return to_update


@dataclass
class DomainNodeModifier(PartialModifier):
    description: TriState[str] = field(default_factory=TriState[str].nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    total_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState[ResourceSlot].nop)
    allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = field(
        default_factory=OptionalState[dict[str, list[str]]].nop
    )
    allowed_docker_registries: OptionalState[list[str]] = field(
        default_factory=OptionalState[list[str]].nop
    )
    integration_id: TriState[str] = field(default_factory=TriState[str].nop)
    dotfiles: OptionalState[bytes] = field(default_factory=OptionalState[bytes].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        self.integration_id.update_dict(to_update, "integration_id")
        self.dotfiles.update_dict(to_update, "dotfiles")
        return to_update
