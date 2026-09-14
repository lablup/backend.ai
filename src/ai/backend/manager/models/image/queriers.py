from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


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
