"""List-read spec for container registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ContainerRegistrySearcher(Searcher[ContainerRegistryRow, ContainerRegistryData]):
    """Container registries matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ContainerRegistryRow)

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()
