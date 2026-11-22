"""What a compute cluster search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.compute_cluster.types import ComputeClusterData, ComputeClusterStatus
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ComputeClusterOwnFields(RowDataConverter[ComputeClusterRow, ComputeClusterData]):
    """The compute cluster's own columns. Only the searchable ones are declared as fields."""

    id = SearchableField(
        ComputeClusterRow.id,
        UUIDConditions(ComputeClusterRow.id),
        ColumnOrder(ComputeClusterRow.id),
    )
    name = SearchableField(
        ComputeClusterRow.name,
        StringConditions(ComputeClusterRow.name),
        ColumnOrder(ComputeClusterRow.name),
    )
    status = SearchableField(
        ComputeClusterRow.status,
        EnumConditions(ComputeClusterRow.status, ComputeClusterStatus),
        ColumnOrder(ComputeClusterRow.status),
    )
    created_at = SearchableField(
        ComputeClusterRow.created_at,
        DateTimeConditions(ComputeClusterRow.created_at),
        ColumnOrder(ComputeClusterRow.created_at),
    )
    updated_at = SearchableField(
        ComputeClusterRow.updated_at,
        DateTimeConditions(ComputeClusterRow.updated_at),
        ColumnOrder(ComputeClusterRow.updated_at),
    )

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterData(
            id=self.id.read(row),
            name=self.name.read(row),
            description=row.description,
            api_server=row.api_server,
            kubeconfig=row.kubeconfig,
            namespace_prefix=row.namespace_prefix,
            gateway_addr=row.gateway_addr,
            gateway_public_key=row.gateway_public_key,
            status=self.status.read(row),
            status_changed_at=row.status_changed_at,
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class ComputeClusterSearchableFields:
    own = _ComputeClusterOwnFields()
