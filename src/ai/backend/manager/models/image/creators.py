"""Insert specs for images and their aliases."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus, ImageType
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ImageCreator(EntityCreator[ImageRow, ImageData]):
    """Creator for an image.

    The image joins the registry it was scanned from; a customized image additionally
    joins the project it is created in. ``creator_id`` records the user it was
    committed for. Both come from the customized-owner label, which the caller reads
    at write time and no read goes back to.
    """

    name: str
    project: str | None
    architecture: str
    registry_id: ContainerRegistryID
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
    creator_id: UserID | None = None
    created_in_project_id: ProjectID | None = None

    @override
    def entity_id(self, row: ImageRow) -> ImageID:
        return ImageID(row.id)

    @override
    def created_in(self, row: ImageRow) -> Collection[EntityIdentifier]:
        if self.created_in_project_id is None:
            return (self.registry_id,)
        return (self.registry_id, self.created_in_project_id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

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
            creator_id=self.creator_id,
        )

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()


@dataclass
class ImageAliasCreator(FieldCreator[ImageID, ImageAliasRow, ImageAliasData]):
    """Creator for one alias of an image."""

    alias: str

    @override
    def field_id(self, row: ImageAliasRow) -> ImageAliasID:
        return ImageAliasID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: ImageID) -> ImageAliasRow:
        return ImageAliasRow(alias=self.alias, image_id=owner_id)

    @override
    def to_data(self, row: ImageAliasRow) -> ImageAliasData:
        return ImageAliasData(id=ImageAliasID(row.id), alias=row.alias or "")
