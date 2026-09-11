from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
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
    is_global: bool | None
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


@dataclass
class PerProjectContainerRegistryInfo:
    """Container registry info resolved from a project's container_registry config.

    Unlike ContainerRegistryData, all fields are non-nullable because
    the data is validated during the lookup process (ProjectRow → ContainerRegistryRow).
    """

    id: ContainerRegistryID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str
    username: str
    password: str
    ssl_verify: bool
    is_global: bool
    extra: dict[str, Any]


@dataclass(frozen=True)
class RegistryProjectChange:
    """Which projects an update starts allowing on a registry, and which it stops.

    Carried with the update rather than applied beside it: the two writes share the
    registry's own transaction, so a refused update leaves the links as they were.
    """

    add: Sequence[ProjectID] = ()
    remove: Sequence[ProjectID] = ()
