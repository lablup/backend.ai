import uuid
from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.container_registry import ContainerRegistryType


@dataclass
class ContainerRegistryData:
    id: uuid.UUID
    url: str
    registry_name: str
    type: ContainerRegistryType
    project: Optional[str]
    username: Optional[str]
    password: Optional[str]
    ssl_verify: Optional[bool]
    is_global: Optional[bool]
    # TODO: Add proper type
    extra: Optional[dict[str, Any]]
