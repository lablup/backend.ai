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
