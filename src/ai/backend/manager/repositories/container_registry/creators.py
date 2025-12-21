"""CreatorSpec implementations for container registry repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ContainerRegistryCreatorSpec(CreatorSpec[ContainerRegistryRow]):
    """CreatorSpec for container registry creation."""

    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: Optional[bool] = None
    project: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_verify: Optional[bool] = None
    extra: Optional[dict[str, Any]] = None
    allowed_groups: Optional[AllowedGroupsModel] = None

    @property
    def has_allowed_groups(self) -> bool:
        """Check if allowed_groups is set and has values to process."""
        return self.allowed_groups is not None and len(self.allowed_groups.add) > 0

    @override
    def build_row(self) -> ContainerRegistryRow:
        return ContainerRegistryRow(
            url=self.url,
            type=self.type,
            registry_name=self.registry_name,
            is_global=self.is_global,
            project=self.project,
            username=self.username,
            password=self.password,
            ssl_verify=self.ssl_verify,
            extra=self.extra,
        )
