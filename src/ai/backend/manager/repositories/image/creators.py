from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ImageAliasCreatorSpec(CreatorSpec[ImageAliasRow]):
    """CreatorSpec for image alias creation."""

    alias: str
    image_id: UUID

    def build_row(self) -> ImageAliasRow:
        return ImageAliasRow(
            alias=self.alias,
            image_id=self.image_id,
        )


@dataclass
class ImageRowCreatorSpec(CreatorSpec[ImageRow]):
    """CreatorSpec that builds an ImageRow from individual fields.

    This spec receives the fields needed to construct an ImageRow
    and creates the instance in build_row().
    """

    name: str
    project: str | None
    architecture: str
    registry_id: UUID
    is_local: bool = False
    registry: str | None = None
    image: str | None = None
    tag: str | None = None
    config_digest: str | None = None
    size_bytes: int | None = None
    type: ImageType | None = None
    accelerators: str | None = None
    labels: dict[str, Any] | None = None
    status: ImageStatus = ImageStatus.ALIVE

    @override
    def build_row(self) -> ImageRow:
        return ImageRow(
            name=self.name,
            project=self.project,
            architecture=self.architecture,
            registry_id=self.registry_id,
            is_local=self.is_local,
            registry=self.registry,
            image=self.image,
            tag=self.tag,
            config_digest=self.config_digest,
            size_bytes=self.size_bytes,
            type=self.type,
            accelerators=self.accelerators,
            labels=self.labels,
            status=self.status,
        )
