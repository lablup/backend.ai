"""Searcher spec for the artifact_registries table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ArtifactRegistrySearcher(Searcher[ArtifactRegistryRow, ArtifactRegistryData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ArtifactRegistryRow)

    @override
    def to_data(self, row: ArtifactRegistryRow) -> ArtifactRegistryData:
        return row.to_dataclass()
