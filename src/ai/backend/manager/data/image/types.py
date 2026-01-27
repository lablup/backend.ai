import enum
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID

from ai.backend.common.types import CIStrEnum, ImageCanonical, ImageID

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
    id: ImageID = field(compare=False)
    name: ImageCanonical
    project: str | None
    image: str
    created_at: datetime | None = field(compare=False)
    tag: str | None
    registry: str
    registry_id: UUID
    architecture: str
    config_digest: str
    size_bytes: int
    is_local: bool
    type: ImageType
    accelerators: str | None
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
    id: ImageID = field(compare=False)
    name: ImageCanonical
    namespace: str
    base_image_name: str
    project: str
    humanized_name: str
    tag: str | None
    tags: list[KVPair]
    version: str | None
    registry: str
    registry_id: UUID
    type: ImageType
    architecture: str
    is_local: bool
    status: ImageStatus
    resource_limits: list[ResourceLimit]
    supported_accelerators: list[str] = field(default_factory=list)
    digest: str | None = field(default=None)
    labels: list[KVPair] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    size_bytes: int = field(default=0)
    # legacy
    hash: str | None = field(default=None)


@dataclass
class ImageAgentInstallStatus:
    """
    Represents the installation status of an image on agents.
    """

    installed: bool
    agent_names: list[str] = field(default_factory=list)


@dataclass
class ImageWithAgentInstallStatus:
    """
    Wraps detailed image information and its agent installation status.
    """

    image: ImageDataWithDetails
    agent_install_status: ImageAgentInstallStatus


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: UUID = field(compare=False)
    alias: str


@dataclass
class ImageListResult:
    """Search result with total count and pagination info for images."""

    items: list[ImageDataWithDetails]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
