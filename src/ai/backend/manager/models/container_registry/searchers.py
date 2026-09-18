"""List-read spec for container registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.container_registry.searchable_fields import (
    ContainerRegistrySearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ContainerRegistrySearcher(Searcher[ContainerRegistryRow, ContainerRegistryData]):
    """Container registries matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ContainerRegistryRow)

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return ContainerRegistrySearchableFields.own.to_data(row)


@dataclass(kw_only=True)
class ContainerRegistryByNameAndProjectSearcher(
    Searcher[ContainerRegistryRow, ContainerRegistryData]
):
    registry_name: str
    project_name: str

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == self.registry_name,
            ContainerRegistryRow.project == self.project_name,
        )

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()
