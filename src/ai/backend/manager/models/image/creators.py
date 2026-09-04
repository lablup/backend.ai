"""Insert specs for images and their aliases."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.docker import LabelName
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus, ImageType
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ImageCreator(EntityCreator[ImageRow, ImageData]):
    """Creator for an image.

    The image joins the registry it was scanned from; a customized image additionally
    joins the user its owner label names, which is what restricts it to that user.
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

    @override
    def entity_id(self, row: ImageRow) -> ImageID:
        return ImageID(row.id)

    @override
    def created_in(self, row: ImageRow) -> Collection[EntityIdentifier]:
        owner = self._customized_owner()
        if owner is None:
            return (self.registry_id,)
        return (self.registry_id, owner)

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
        )

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()

    def _customized_owner(self) -> UserID | None:
        """The user a customized image belongs to, read off its owner label."""
        owner_label = (self.labels or {}).get(LabelName.CUSTOMIZED_OWNER)
        if owner_label is None:
            return None
        prefix, sep, owner_id = owner_label.partition(":")
        if prefix and sep and owner_id:
            try:
                return UserID(uuid.UUID(owner_id))
            except ValueError:
                pass
        log.warning("Invalid {} label value: {!r}", LabelName.CUSTOMIZED_OWNER, owner_label)
        return None


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
