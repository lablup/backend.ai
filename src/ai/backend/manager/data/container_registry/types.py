import uuid
from dataclasses import dataclass
from typing import Any, Optional, TypedDict

from ai.backend.common.container_registry import ContainerRegistryType


@dataclass
class HarborProjectInfo:
    url: str
    project: str
    ssl_verify: bool


class HarborAuthArgs(TypedDict):
    username: str
    password: str


class HarborProjectQuotaInfo(TypedDict):
    previous_quota: int
    quota_id: int


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
