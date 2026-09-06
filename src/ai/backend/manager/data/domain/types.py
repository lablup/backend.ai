from __future__ import annotations

import enum
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


class DomainStatus(enum.StrEnum):
    """Lifecycle status of a domain."""

    ACTIVE = "active"
    DELETED = "deleted"
    PURGING = "purging"
    PURGE_ERROR = "purge-error"

    @classmethod
    def purge_in_progress(cls) -> frozenset[DomainStatus]:
        """Statuses a purge is working through. Writes are refused while in one."""
        return frozenset({cls.PURGING, cls.PURGE_ERROR})


@dataclass
class UserInfo:
    id: uuid.UUID
    role: UserRole
    domain_name: str


@dataclass
class DomainData(EntityData):
    id: DomainID
    name: str
    description: str | None
    is_active: bool
    is_default: bool
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: VFolderHostPermissionMap
    allowed_docker_registries: list[str]
    dotfiles: bytes
    integration_name: str | None

    @override
    def entity_id(self) -> DomainID:
        return self.id

    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type=ScopeType.DOMAIN,
            scope_id=str(self.id),
        )

    def role_name(self) -> str:
        return f"domain-{self.name}-admin"

    def entity_operations(self) -> Mapping[RBACElementType, Iterable[OperationType]]:
        operations: dict[RBACElementType, Iterable[OperationType]] = {
            entity.to_element(): OperationType.admin_operations()
            for entity in EntityType.admin_accessible_entity_types_in_domain()
        }
        operations[RBACElementType.DOMAIN_ADMIN_PAGE] = {OperationType.READ}
        return operations


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
    integration_name: TriState[str] = field(default_factory=TriState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        # Field is named integration_name above model layer; DB column remains integration_id.
        self.integration_name.update_dict(to_update, "integration_id")
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
    integration_name: TriState[str] = field(default_factory=TriState[str].nop)
    dotfiles: OptionalState[bytes] = field(default_factory=OptionalState[bytes].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        self.is_active.update_dict(to_update, "is_active")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.allowed_docker_registries.update_dict(to_update, "allowed_docker_registries")
        # Field is named integration_name above model layer; DB column remains integration_id.
        self.integration_name.update_dict(to_update, "integration_id")
        self.dotfiles.update_dict(to_update, "dotfiles")
        return to_update
