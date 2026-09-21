"""What a preset category search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _PrometheusQueryPresetCategoryOwnFields(
    RowDataConverter[PrometheusQueryPresetCategoryRow, PrometheusQueryPresetCategoryData]
):
    """The category's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches.
    """

    id = SearchableField(
        PrometheusQueryPresetCategoryRow.id,
        UUIDConditions(PrometheusQueryPresetCategoryRow.id),
        ColumnOrder(PrometheusQueryPresetCategoryRow.id),
    )
    name = SearchableField(
        PrometheusQueryPresetCategoryRow.name,
        StringConditions(PrometheusQueryPresetCategoryRow.name),
        ColumnOrder(PrometheusQueryPresetCategoryRow.name),
    )
    description = SearchableField(PrometheusQueryPresetCategoryRow.description, None, None)
    created_at = SearchableField(
        PrometheusQueryPresetCategoryRow.created_at,
        DateTimeConditions(PrometheusQueryPresetCategoryRow.created_at),
        ColumnOrder(PrometheusQueryPresetCategoryRow.created_at),
    )
    updated_at = SearchableField(
        PrometheusQueryPresetCategoryRow.updated_at,
        DateTimeConditions(PrometheusQueryPresetCategoryRow.updated_at),
        ColumnOrder(PrometheusQueryPresetCategoryRow.updated_at),
    )

    @override
    def to_data(self, row: PrometheusQueryPresetCategoryRow) -> PrometheusQueryPresetCategoryData:
        return PrometheusQueryPresetCategoryData(
            id=PrometheusQueryPresetCategoryID(self.id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class PrometheusQueryPresetCategorySearchableFields:
    own = _PrometheusQueryPresetCategoryOwnFields()
