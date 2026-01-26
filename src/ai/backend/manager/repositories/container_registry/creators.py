"""CreatorSpec implementations for container registry repository."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ContainerRegistryCreatorSpec(CreatorSpec[ContainerRegistryRow]):
    """CreatorSpec for container registry creation."""

    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: bool | None = None
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    extra: dict[str, Any] | None = None
    allowed_groups: AllowedGroupsModel | None = None

    @property
    def has_allowed_groups(self) -> bool:
        """Check if allowed_groups is set and has values to process."""
        return self.allowed_groups is not None and len(self.allowed_groups.add) > 0

    @override
    def build_row(self) -> ContainerRegistryRow:
        return ContainerRegistryRow(
            id=uuid.uuid4(),
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
