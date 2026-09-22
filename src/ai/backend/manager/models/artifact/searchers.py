"""Searcher specs for the artifacts table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactDataWithRevisions
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.searchable_fields import (
    ArtifactSearchableFields,
)
from ai.backend.manager.models.artifact_revision.searchable_fields import (
    ArtifactRevisionSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ArtifactSearcher(Searcher[ArtifactRow, ArtifactData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRow)

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return ArtifactSearchableFields.own.to_data(row)


@dataclass
class ArtifactWithRevisionsSearcher(Searcher[ArtifactRow, ArtifactDataWithRevisions]):
    """Reads artifacts with their revisions eagerly loaded."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRow).options(selectinload(ArtifactRow.revision_rows))

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactDataWithRevisions:
        return ArtifactDataWithRevisions.from_dataclasses(
            artifact_data=ArtifactSearchableFields.own.to_data(row),
            revisions=[
                ArtifactRevisionSearchableFields.own.to_data(revision)
                for revision in row.revision_rows
            ],
        )
