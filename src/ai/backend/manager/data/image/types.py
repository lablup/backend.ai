import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional

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
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: uuid.UUID = field(compare=False)
    alias: str
