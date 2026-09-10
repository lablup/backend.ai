"""Purge specs for the images table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ImagePurger(EntityPurger[ImageRow, ImageData]):
    """Removes an image along with the scope it was; its aliases go with it through
    the FK cascade."""

    image_id: ImageID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.image_id

    @override
    def row_class(self) -> type[ImageRow]:
        return ImageRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ImageRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()
