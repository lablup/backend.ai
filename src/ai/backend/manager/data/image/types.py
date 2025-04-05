import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ai.backend.manager.models.image import ImageStatus, ImageType


@dataclass
class ImageLabelsData:
    label_data: dict[str, str]


@dataclass
class ImageResourcesData:
    resources_data: dict[str, dict[str, Optional[str]]]


@dataclass
class ImageData:
    id: uuid.UUID
    name: str
    project: Optional[str]
    image: str
    created_at: Optional[datetime]
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
class PurgeImageResponseData:
    image_canonical: str


@dataclass
class ImageAliasData:
    id: uuid.UUID
    alias: str
