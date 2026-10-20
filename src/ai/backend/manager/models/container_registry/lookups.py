"""Lookup implementations for the container registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
    ContainerRegistryName,
    ContainerRegistryProjectName,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ContainerRegistryByNameAndRegistryProjectLookup(
    DataLookup[ContainerRegistryRow, ContainerRegistryID]
):
    """Resolves a registry name and its internal project name into the registry they name."""

    registry_name: ContainerRegistryName
    registry_project_name: ContainerRegistryProjectName | None

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def entity_type(self) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        # A None project renders as IS NULL, which is how a registry without one is named.
        return [
            lambda: ContainerRegistryRow.registry_name == self.registry_name,
            lambda: ContainerRegistryRow.project == self.registry_project_name,
        ]

    @override
    def to_entity_id(self, row: ContainerRegistryRow) -> ContainerRegistryID:
        return row.id
