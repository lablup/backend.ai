from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.types import EntityData


@dataclass
class ContainerRegistryData(EntityData):
    id: ContainerRegistryID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str | None
    username: str | None
    password: str | None
    ssl_verify: bool | None
    is_global: bool
    # TODO: Add proper type
    extra: dict[str, Any] | None

    @override
    def entity_id(self) -> ContainerRegistryID:
        return self.id


@dataclass
class ContainerRegistrySearchResult:
    """Search result with pagination for container registries."""

    items: list[ContainerRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ImageCommitRegistry:
    registry_name: str
    project_name: str | None

    def to_json(self) -> dict[str, str | None]:
        return {"registry": self.registry_name, "project": self.project_name}
