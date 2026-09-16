from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.image import ImageID
from ai.backend.manager.data.image.types import ImageAliasData, ImageData
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.specs.querier import (
    BulkEntityQuerier,
    BulkFieldQuerier,
    DataQuerier,
)


@dataclass
class ImageQuerier(DataQuerier[ImageRow, ImageData]):
    """Reads one image by id."""

    image_id: ImageID

    @override
    def row_class(self) -> type[ImageRow]:
        return ImageRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ImageRow.id

    @override
    def entity_id_value(self) -> ImageID:
        return self.image_id

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()


class BulkImageQuerier(BulkEntityQuerier[ImageRow, ImageData]):
    """The images the caller named."""

    @override
    def row_class(self) -> type[ImageRow]:
        return ImageRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ImageRow.id

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()


class BulkImageAliasQuerier(BulkFieldQuerier[ImageAliasRow, ImageAliasData]):
    """The image aliases the caller named."""

    @override
    def row_class(self) -> type[ImageAliasRow]:
        return ImageAliasRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ImageAliasRow.id

    @override
    def to_data(self, row: ImageAliasRow) -> ImageAliasData:
        return row.to_dataclass()
