import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from ai.backend.common.types import CIStrEnum

if TYPE_CHECKING:
    from ai.backend.manager.models.image import Resources


class ImageStatus(enum.StrEnum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"


class ImageType(CIStrEnum):
    COMPUTE = "compute"
    SYSTEM = "system"
    SERVICE = "service"


class ImageIdentifier(NamedTuple):
    """
    Represent a tuple of image's canonical string and architecture, uniquely corresponding to an ImageRow.
    """

    canonical: str
    architecture: str


@dataclass
class ImageLabelsData:
    label_data: dict[str, str]


@dataclass
class ImageResourcesData:
    resources_data: "Resources"


@dataclass
class ImageData:
    id: uuid.UUID = field(compare=False)
    name: str
    project: Optional[str]
    image: str
    created_at: Optional[datetime] = field(compare=False)
    tag: Optional[str]
    registry: str
    registry_id: uuid.UUID
    architecture: str
    config_digest: str
    size_bytes: int
    is_local: bool
    type: ImageType
    accelerators: Optional[str]
    labels: ImageLabelsData
    resources: ImageResourcesData
    status: ImageStatus


@dataclass
class KVPair:
    key: str
    value: str


@dataclass
class ResourceLimit:
    key: str
    min: Decimal
    max: Decimal


@dataclass
class ImageDataWithDetails:
    id: uuid.UUID = field(compare=False)
    name: str
    namespace: str
    base_image_name: str
    project: str
    humanized_name: str
    tag: Optional[str]
    tags: list[KVPair]
    version: Optional[str]
    registry: str
    architecture: str
    is_local: bool
    status: ImageStatus
    resource_limits: list[ResourceLimit]
    supported_accelerators: list[str] = field(default_factory=list)
    digest: Optional[str] = field(default=None)
    labels: list[KVPair] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    size_bytes: int = field(default=0)
    # legacy
    hash: Optional[str] = field(default=None)
    raw_labels: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageAgentStatus:
    """
    Represents the installation status of an image on agents.
    """

    installed: bool
    agent_names: list[str] = field(default_factory=list)


@dataclass
class ImageWithAgentStatus:
    """
    Wraps detailed image information and its agent installation status.
    """

    image: ImageDataWithDetails
    agent_status: ImageAgentStatus


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: uuid.UUID = field(compare=False)
    alias: str
