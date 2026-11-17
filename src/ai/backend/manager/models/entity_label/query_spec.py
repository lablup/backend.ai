"""The label fields a search can filter and order by, and how a labelable entity reaches them."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import QueryColumn


class _EntityLabelOwnColumns:
    """The label's own columns."""

    field_id = QueryColumn(
        EntityLabelRow.id, UUIDConditions(EntityLabelRow.id), ColumnOrder(EntityLabelRow.id)
    )
    key = QueryColumn(
        EntityLabelRow.key, StringConditions(EntityLabelRow.key), ColumnOrder(EntityLabelRow.key)
    )
    value = QueryColumn(
        EntityLabelRow.value,
        StringConditions(EntityLabelRow.value),
        ColumnOrder(EntityLabelRow.value),
    )
    entity_type = QueryColumn(
        EntityLabelRow.entity_type,
        StringConditions(EntityLabelRow.entity_type),
        ColumnOrder(EntityLabelRow.entity_type),
    )
    entity_id = QueryColumn(
        EntityLabelRow.entity_id,
        UUIDConditions(EntityLabelRow.entity_id),
        ColumnOrder(EntityLabelRow.entity_id),
    )
    created_at = QueryColumn(
        EntityLabelRow.created_at,
        DateTimeConditions(EntityLabelRow.created_at),
        ColumnOrder(EntityLabelRow.created_at),
    )


class EntityLabelQuerySpec:
    own = _EntityLabelOwnColumns


class EntityLabelCorrelation(ToManyCorrelation):
    """The labels on one labelable entity, matched by entity type and id."""

    def __init__(
        self,
        owner_row: type[Any],
        owner_type: EntityType,
        owner_id: InstrumentedAttribute[Any],
    ) -> None:
        super().__init__(
            child_row=EntityLabelRow,
            correlate_row=owner_row,
            join_predicate=sa.and_(
                EntityLabelRow.entity_id == owner_id,
                EntityLabelRow.entity_type == owner_type,
            ),
        )
