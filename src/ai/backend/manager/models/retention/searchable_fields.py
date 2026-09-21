"""What a retention policy search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _RetentionPolicyOwnFields(RowDataConverter[RetentionPolicyRow, RetentionPolicyData]):
    """The retention policy's own columns."""

    id = SearchableField(
        RetentionPolicyRow.id,
        UUIDConditions(RetentionPolicyRow.id),
        ColumnOrder(RetentionPolicyRow.id),
    )
    category = SearchableField(
        RetentionPolicyRow.category,
        EnumConditions(RetentionPolicyRow.category, RetentionCategory),
        ColumnOrder(RetentionPolicyRow.category),
    )
    retention_period = SearchableField(
        RetentionPolicyRow.retention_period, None, ColumnOrder(RetentionPolicyRow.retention_period)
    )
    """No shared condition class covers ``sa.Interval``, so the filter slot stays empty."""
    enabled = SearchableField(
        RetentionPolicyRow.enabled,
        BoolConditions(RetentionPolicyRow.enabled),
        ColumnOrder(RetentionPolicyRow.enabled),
    )
    last_swept_at = SearchableField(
        RetentionPolicyRow.last_swept_at,
        DateTimeConditions(RetentionPolicyRow.last_swept_at),
        ColumnOrder(RetentionPolicyRow.last_swept_at),
    )
    created_at = SearchableField(
        RetentionPolicyRow.created_at,
        DateTimeConditions(RetentionPolicyRow.created_at),
        ColumnOrder(RetentionPolicyRow.created_at),
    )
    updated_at = SearchableField(
        RetentionPolicyRow.updated_at,
        DateTimeConditions(RetentionPolicyRow.updated_at),
        ColumnOrder(RetentionPolicyRow.updated_at),
    )

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return RetentionPolicyData(
            id=RetentionPolicyID(self.id.read(row)),
            category=self.category.read(row),
            retention_period=self.retention_period.read(row),
            enabled=self.enabled.read(row),
            last_swept_at=self.last_swept_at.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class RetentionPolicySearchableFields:
    own = _RetentionPolicyOwnFields()
