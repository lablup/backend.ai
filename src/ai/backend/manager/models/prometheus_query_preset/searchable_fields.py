"""What a prometheus query preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _PrometheusQueryPresetOwnFields(
    RowDataConverter[PrometheusQueryPresetRow, PrometheusQueryPresetData]
):
    """The preset's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches, and ``options``
    is JSON. ``filter_labels`` and ``group_labels`` are derived — they are read out of
    ``options`` — so they carry no field and are built in :meth:`to_data`.
    """

    id = SearchableField(
        PrometheusQueryPresetRow.id,
        UUIDConditions(PrometheusQueryPresetRow.id),
        ColumnOrder(PrometheusQueryPresetRow.id),
    )
    name = SearchableField(
        PrometheusQueryPresetRow.name,
        StringConditions(PrometheusQueryPresetRow.name),
        ColumnOrder(PrometheusQueryPresetRow.name),
    )
    metric_name = SearchableField(
        PrometheusQueryPresetRow.metric_name,
        StringConditions(PrometheusQueryPresetRow.metric_name),
        ColumnOrder(PrometheusQueryPresetRow.metric_name),
    )
    query_template = SearchableField(
        PrometheusQueryPresetRow.query_template,
        StringEqualityConditions(PrometheusQueryPresetRow.query_template),
        ColumnOrder(PrometheusQueryPresetRow.query_template),
    )
    time_window = SearchableField(
        PrometheusQueryPresetRow.time_window,
        StringConditions(PrometheusQueryPresetRow.time_window),
        ColumnOrder(PrometheusQueryPresetRow.time_window),
    )
    description = SearchableField(PrometheusQueryPresetRow.description, None, None)
    rank = SearchableField(
        PrometheusQueryPresetRow.rank,
        IntConditions(PrometheusQueryPresetRow.rank),
        ColumnOrder(PrometheusQueryPresetRow.rank),
    )
    category_id = SearchableField(
        PrometheusQueryPresetRow.category_id,
        UUIDConditions(PrometheusQueryPresetRow.category_id),
        ColumnOrder(PrometheusQueryPresetRow.category_id),
    )
    options = SearchableField(PrometheusQueryPresetRow.options, None, None)
    created_at = SearchableField(
        PrometheusQueryPresetRow.created_at,
        DateTimeConditions(PrometheusQueryPresetRow.created_at),
        ColumnOrder(PrometheusQueryPresetRow.created_at),
    )
    updated_at = SearchableField(
        PrometheusQueryPresetRow.updated_at,
        DateTimeConditions(PrometheusQueryPresetRow.updated_at),
        ColumnOrder(PrometheusQueryPresetRow.updated_at),
    )

    @override
    def to_data(self, row: PrometheusQueryPresetRow) -> PrometheusQueryPresetData:
        category_id = self.category_id.read(row)
        options = self.options.read(row)
        return PrometheusQueryPresetData(
            id=PrometheusQueryPresetID(self.id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            rank=self.rank.read(row),
            category_id=(
                PrometheusQueryPresetCategoryID(category_id) if category_id is not None else None
            ),
            metric_name=self.metric_name.read(row),
            query_template=self.query_template.read(row),
            time_window=self.time_window.read(row),
            filter_labels=options.filter_labels,
            group_labels=options.group_labels,
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class PrometheusQueryPresetSearchableFields:
    own = _PrometheusQueryPresetOwnFields()
