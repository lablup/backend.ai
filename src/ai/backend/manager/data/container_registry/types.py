import uuid
from dataclasses import dataclass
from typing import Any

from ai.backend.common.container_registry import ContainerRegistryType


@dataclass
class ContainerRegistryData:
    id: uuid.UUID
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


@dataclass
class PerProjectContainerRegistryInfo:
    """Container registry info resolved from a project's container_registry config.

    Unlike ContainerRegistryData, all fields are non-nullable because
    the data is validated during the lookup process (GroupRow → ContainerRegistryRow).
    """

    id: uuid.UUID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: str
    username: str
    password: str
    ssl_verify: bool
    is_global: bool
    extra: dict[str, Any]
