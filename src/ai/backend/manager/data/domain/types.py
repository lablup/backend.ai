from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, override

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.types import OptionalState, PartialModifier, TriState

if TYPE_CHECKING:
    from ai.backend.manager.models.domain import DomainRow


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

    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type=ScopeType.DOMAIN,
            scope_id=self.name,
        )

    def role_name(self) -> str:
        return f"domain-{self.name}-admin"

    def entity_operations(self) -> Mapping[EntityType, Iterable[OperationType]]:
        return {
            entity: OperationType.admin_operations()
            for entity in EntityType.admin_accessible_entity_types_in_domain()
        }


@dataclass
class DomainCreator(CreatorSpec["DomainRow"]):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = None
    total_resource_slots: Optional[ResourceSlot] = None
    allowed_vfolder_hosts: Optional[dict[str, list[str]]] = None
    allowed_docker_registries: Optional[list[str]] = None
    integration_id: Optional[str] = None
    dotfiles: Optional[bytes] = None

    @override
    def build_row(self) -> DomainRow:
        from ai.backend.manager.models.domain import DomainRow

        return DomainRow(
            name=self.name,
            description=self.description,
            is_active=self.is_active if self.is_active is not None else True,
            total_resource_slots=self.total_resource_slots if self.total_resource_slots else {},
            allowed_vfolder_hosts=self.allowed_vfolder_hosts if self.allowed_vfolder_hosts else {},
            allowed_docker_registries=self.allowed_docker_registries
            if self.allowed_docker_registries
            else [],
            integration_id=self.integration_id,
            dotfiles=self.dotfiles if self.dotfiles else b"\x90",
        )


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
