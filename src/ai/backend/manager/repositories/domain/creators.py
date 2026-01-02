"""CreatorSpec implementations for domain repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typing_extensions import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DomainCreatorSpec(CreatorSpec[DomainRow]):
    """CreatorSpec for domain creation."""

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
