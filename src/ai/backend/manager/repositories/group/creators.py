"""CreatorSpec implementations for group repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class GroupCreatorSpec(CreatorSpec[GroupRow]):
    """CreatorSpec for group creation."""

    name: str
    domain_name: str
    type: ProjectType | None = None
    description: str | None = None
    is_active: bool | None = None
    total_resource_slots: ResourceSlot | None = None
    allowed_vfolder_hosts: VFolderHostPermissionMap | None = None
    integration_id: str | None = None
    resource_policy: str | None = None
    container_registry: dict[str, str] | None = None
    dotfiles: bytes | None = None

    @override
    def build_row(self) -> GroupRow:
        return GroupRow(
            name=self.name,
            domain_name=self.domain_name,
            type=self.type or ProjectType.GENERAL,
            description=self.description,
            is_active=self.is_active if self.is_active is not None else True,
            total_resource_slots=self.total_resource_slots or {},
            allowed_vfolder_hosts=self.allowed_vfolder_hosts or VFolderHostPermissionMap(),
            integration_id=self.integration_id,
            resource_policy=self.resource_policy,
            dotfiles=self.dotfiles,
            container_registry=self.container_registry,
        )
