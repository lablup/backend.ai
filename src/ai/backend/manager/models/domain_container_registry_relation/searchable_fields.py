"""What a domain container registry relation search can filter and order by, and how its row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.container_registry.types import DomainContainerRegistryRelationData
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _DomainContainerRegistryRelationOwnFields(
    RowDataConverter[DomainContainerRegistryRelationRow, DomainContainerRegistryRelationData]
):
    domain_id = SearchableField(
        DomainContainerRegistryRelationRow.domain_id,
        UUIDConditions(DomainContainerRegistryRelationRow.domain_id),
        ColumnOrder(DomainContainerRegistryRelationRow.domain_id),
    )
    container_registry_id = SearchableField(
        DomainContainerRegistryRelationRow.container_registry_id,
        UUIDConditions(DomainContainerRegistryRelationRow.container_registry_id),
        ColumnOrder(DomainContainerRegistryRelationRow.container_registry_id),
    )

    @override
    def to_data(
        self, row: DomainContainerRegistryRelationRow
    ) -> DomainContainerRegistryRelationData:
        return DomainContainerRegistryRelationData(
            domain_id=self.domain_id.read(row),
            container_registry_id=self.container_registry_id.read(row),
        )


class DomainContainerRegistryRelationSearchableFields:
    own = _DomainContainerRegistryRelationOwnFields()
