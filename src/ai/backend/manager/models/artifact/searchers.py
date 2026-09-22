"""Searcher specs for the artifacts table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact.searchable_fields import (
    ArtifactSearchableFields,
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
