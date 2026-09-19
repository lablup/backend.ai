from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier, DataQuerier


@dataclass
class ContainerRegistryQuerier(DataQuerier[ContainerRegistryRow, ContainerRegistryData]):
    """Reads one container registry by its id."""

    registry_id: ContainerRegistryID

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ContainerRegistryRow.id

    @override
    def entity_id_value(self) -> ContainerRegistryID:
        return self.registry_id

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()


class BulkContainerRegistryQuerier(BulkEntityQuerier[ContainerRegistryRow, ContainerRegistryData]):
    """The container registries the caller named."""

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ContainerRegistryRow.id

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()
