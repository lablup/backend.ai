"""Searcher spec for the reservoir_registries table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import with_expression

from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.reservoir_registry.searchable_fields import (
    ReservoirRegistrySearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ReservoirRegistrySearcher(Searcher[ReservoirRegistryRow, ReservoirRegistryData]):
    """The name is the artifact_registries row's, so every read joins it."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(ReservoirRegistryRow)
            .join(
                ArtifactRegistryRow,
                ArtifactRegistryRow.registry_id == ReservoirRegistryRow.id,
            )
            .options(with_expression(ReservoirRegistryRow.registry_name, ArtifactRegistryRow.name))
        )

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryData:
        return ReservoirRegistrySearchableFields.own.to_data(row)
