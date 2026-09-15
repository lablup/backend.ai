"""List-read specs for images."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ImageSearcher(Searcher[ImageRow, ImageData]):
    """Images matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ImageRow)

    @override
    def to_data(self, row: ImageRow) -> ImageData:
        return row.to_dataclass()
