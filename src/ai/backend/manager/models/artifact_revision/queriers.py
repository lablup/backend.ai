"""FieldQuerier implementations for artifact revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.querier import FieldQuerier


@dataclass
class ArtifactRevisionQuerier(FieldQuerier[ArtifactRevisionRow, ArtifactRevisionData]):
    revision_id: ArtifactRevisionID

    @override
    def row_class(self) -> type[ArtifactRevisionRow]:
        return ArtifactRevisionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRevisionRow.id

    @override
    def target_id_value(self) -> ArtifactRevisionID:
        return self.revision_id

    @override
    def to_data(self, row: ArtifactRevisionRow) -> ArtifactRevisionData:
        return row.to_dataclass()
