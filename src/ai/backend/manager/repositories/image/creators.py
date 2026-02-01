"""CreatorSpec implementations for image repository."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ai.backend.manager.models.image.row import ImageAliasRow
from ai.backend.manager.repositories.base import CreatorSpec


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
