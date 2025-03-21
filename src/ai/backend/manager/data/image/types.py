import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Self

from ai.backend.manager.models.image import ImageRow, ImageStatus, ImageType


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
    # TODO: 타입 정의 필요
    labels: dict[str, Any]
    # TODO: 타입 정의 필요
    resources: dict[str, dict[str, Optional[str]]]
    status: ImageStatus

    @classmethod
    def from_image_row(cls, row: ImageRow) -> Self:
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
            labels=row.labels,
            resources=row.resources,
            status=row.status,
        )

    def to_image_row(self) -> ImageRow:
        return ImageRow(
            name=self.name,
            project=self.project,
            image=self.image,
            created_at=self.created_at,
            tag=self.tag,
            registry=self.registry,
            registry_id=self.registry_id,
            architecture=self.architecture,
            config_digest=self.config_digest,
            size_bytes=self.size_bytes,
            is_local=self.is_local,
            type=self.type,
            accelerators=self.accelerators,
            labels=self.labels,
            resources=self.resources,
            status=self.status,
        )


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: uuid.UUID
    alias: str
