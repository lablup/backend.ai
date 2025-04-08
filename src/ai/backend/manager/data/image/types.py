import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Self

from ai.backend.manager.models.image import ImageRow, ImageStatus, ImageType


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

    @classmethod
    def from_row(cls, row: Optional[ImageRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            name=row.name,
            project=row.project,
            image=row.image,
            created_at=row.created_at,
            tag=row.tag,
            registry=row.registry,
            registry_id=row.registry_id,
            architecture=row.architecture,
            config_digest=row.config_digest,
            size_bytes=row.size_bytes,
            is_local=row.is_local,
            type=row.type,
            accelerators=row.accelerators,
            labels=ImageLabelsData(label_data=row.labels),
            resources=ImageResourcesData(resources_data=row.resources),
            status=row.status,
        )


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: uuid.UUID
    alias: str
