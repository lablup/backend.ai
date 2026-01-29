"""CreatorSpec implementations for domain repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DomainCreatorSpec(CreatorSpec[DomainRow]):
    """CreatorSpec for domain creation."""

    name: str
    description: str | None = None
    is_active: bool | None = None
    total_resource_slots: ResourceSlot | None = None
    allowed_vfolder_hosts: dict[str, list[str]] | None = None
    allowed_docker_registries: list[str] | None = None
    integration_id: str | None = None
    dotfiles: bytes | None = None

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
