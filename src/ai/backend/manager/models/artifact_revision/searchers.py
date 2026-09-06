"""Searcher spec for the artifact_revisions table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ArtifactRevisionSearcher(Searcher[ArtifactRevisionRow, ArtifactRevisionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRevisionRow)

    @override
    def to_data(self, row: ArtifactRevisionRow) -> ArtifactRevisionData:
        return row.to_dataclass()
