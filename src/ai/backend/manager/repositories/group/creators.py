"""CreatorSpec implementations for group repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typing_extensions import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class GroupCreatorSpec(CreatorSpec[GroupRow]):
    """CreatorSpec for group creation."""

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

    @override
    def build_row(self) -> GroupRow:
        return GroupRow(
            name=self.name,
            domain_name=self.domain_name,
            type=self.type or ProjectType.GENERAL,
            description=self.description,
            is_active=self.is_active if self.is_active is not None else True,
            total_resource_slots=self.total_resource_slots or {},
            allowed_vfolder_hosts=self.allowed_vfolder_hosts or {},
            integration_id=self.integration_id,
            resource_policy=self.resource_policy,
            dotfiles=self.dotfiles,
            container_registry=self.container_registry,
        )
