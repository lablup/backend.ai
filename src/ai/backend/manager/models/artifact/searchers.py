"""Searcher specs for the artifacts table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactDataWithRevisions
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ArtifactSearcher(Searcher[ArtifactRow, ArtifactData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRow)

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()


@dataclass
class ArtifactWithRevisionsSearcher(Searcher[ArtifactRow, ArtifactDataWithRevisions]):
    """Reads artifacts with their revisions eagerly loaded."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRow).options(selectinload(ArtifactRow.revision_rows))

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactDataWithRevisions:
        return ArtifactDataWithRevisions.from_dataclasses(
            artifact_data=row.to_dataclass(),
            revisions=[revision.to_dataclass() for revision in row.revision_rows],
        )
