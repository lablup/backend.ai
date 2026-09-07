"""BulkEntityQuerier implementation for the artifacts table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkArtifactQuerier(BulkEntityQuerier[ArtifactRow, ArtifactData]):
    """The artifacts the caller named."""

    @override
    def row_class(self) -> type[ArtifactRow]:
        return ArtifactRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRow.id

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()
