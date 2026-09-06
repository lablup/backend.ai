"""Searcher spec for the reservoir_registries table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ReservoirRegistrySearcher(Searcher[ReservoirRegistryRow, ReservoirRegistryData]):
    """The name is the meta row's, so every read loads it."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ReservoirRegistryRow).options(selectinload(ReservoirRegistryRow.meta))

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryData:
        return row.to_dataclass()
