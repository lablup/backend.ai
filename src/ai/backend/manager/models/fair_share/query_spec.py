"""What a fair share search can filter and order by.

No ``RowDataConverter`` here: a fair share data type carries the resource group's
default weight and the cluster's available slots merged into the row's values, and
neither is on the row. The merge stays on the row class.
"""

from __future__ import annotations

from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.specs.conditions.date import DateConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import QueryColumn


class _DomainFairShareOwnColumns:
    """The domain fair share's own columns."""

    id = QueryColumn(
        DomainFairShareRow.id,
        UUIDConditions(DomainFairShareRow.id),
        ColumnOrder(DomainFairShareRow.id),
    )
    resource_group = QueryColumn(
        DomainFairShareRow.resource_group,
        StringConditions(DomainFairShareRow.resource_group),
        ColumnOrder(DomainFairShareRow.resource_group),
    )
    resource_group_id = QueryColumn(
        DomainFairShareRow.resource_group_id,
        UUIDConditions(DomainFairShareRow.resource_group_id),
        ColumnOrder(DomainFairShareRow.resource_group_id),
    )
    domain_name = QueryColumn(
        DomainFairShareRow.domain_name,
        StringConditions(DomainFairShareRow.domain_name),
        ColumnOrder(DomainFairShareRow.domain_name),
    )
    weight = QueryColumn(
        DomainFairShareRow.weight,
        DecimalConditions(DomainFairShareRow.weight),
        ColumnOrder(DomainFairShareRow.weight),
    )
    fair_share_factor = QueryColumn(
        DomainFairShareRow.fair_share_factor,
        DecimalConditions(DomainFairShareRow.fair_share_factor),
        ColumnOrder(DomainFairShareRow.fair_share_factor),
    )
    normalized_usage = QueryColumn(
        DomainFairShareRow.normalized_usage,
        DecimalConditions(DomainFairShareRow.normalized_usage),
        ColumnOrder(DomainFairShareRow.normalized_usage),
    )
    total_decayed_usage = QueryColumn(DomainFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = QueryColumn(DomainFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = QueryColumn(
        DomainFairShareRow.last_calculated_at,
        DateTimeConditions(DomainFairShareRow.last_calculated_at),
        ColumnOrder(DomainFairShareRow.last_calculated_at),
    )
    lookback_start = QueryColumn(
        DomainFairShareRow.lookback_start,
        DateConditions(DomainFairShareRow.lookback_start),
        ColumnOrder(DomainFairShareRow.lookback_start),
    )
    lookback_end = QueryColumn(
        DomainFairShareRow.lookback_end,
        DateConditions(DomainFairShareRow.lookback_end),
        ColumnOrder(DomainFairShareRow.lookback_end),
    )
    half_life_days = QueryColumn(
        DomainFairShareRow.half_life_days,
        IntConditions(DomainFairShareRow.half_life_days),
        ColumnOrder(DomainFairShareRow.half_life_days),
    )
    lookback_days = QueryColumn(
        DomainFairShareRow.lookback_days,
        IntConditions(DomainFairShareRow.lookback_days),
        ColumnOrder(DomainFairShareRow.lookback_days),
    )
    decay_unit_days = QueryColumn(
        DomainFairShareRow.decay_unit_days,
        IntConditions(DomainFairShareRow.decay_unit_days),
        ColumnOrder(DomainFairShareRow.decay_unit_days),
    )
    created_at = QueryColumn(
        DomainFairShareRow.created_at,
        DateTimeConditions(DomainFairShareRow.created_at),
        ColumnOrder(DomainFairShareRow.created_at),
    )
    updated_at = QueryColumn(
        DomainFairShareRow.updated_at,
        DateTimeConditions(DomainFairShareRow.updated_at),
        ColumnOrder(DomainFairShareRow.updated_at),
    )


class DomainFairShareQuerySpec:
    own = _DomainFairShareOwnColumns()


class _ProjectFairShareOwnColumns:
    """The project fair share's own columns."""

    id = QueryColumn(
        ProjectFairShareRow.id,
        UUIDConditions(ProjectFairShareRow.id),
        ColumnOrder(ProjectFairShareRow.id),
    )
    resource_group = QueryColumn(
        ProjectFairShareRow.resource_group,
        StringConditions(ProjectFairShareRow.resource_group),
        ColumnOrder(ProjectFairShareRow.resource_group),
    )
    resource_group_id = QueryColumn(
        ProjectFairShareRow.resource_group_id,
        UUIDConditions(ProjectFairShareRow.resource_group_id),
        ColumnOrder(ProjectFairShareRow.resource_group_id),
    )
    project_id = QueryColumn(
        ProjectFairShareRow.project_id,
        UUIDConditions(ProjectFairShareRow.project_id),
        ColumnOrder(ProjectFairShareRow.project_id),
    )
    domain_name = QueryColumn(
        ProjectFairShareRow.domain_name,
        StringConditions(ProjectFairShareRow.domain_name),
        ColumnOrder(ProjectFairShareRow.domain_name),
    )
    weight = QueryColumn(
        ProjectFairShareRow.weight,
        DecimalConditions(ProjectFairShareRow.weight),
        ColumnOrder(ProjectFairShareRow.weight),
    )
    fair_share_factor = QueryColumn(
        ProjectFairShareRow.fair_share_factor,
        DecimalConditions(ProjectFairShareRow.fair_share_factor),
        ColumnOrder(ProjectFairShareRow.fair_share_factor),
    )
    normalized_usage = QueryColumn(
        ProjectFairShareRow.normalized_usage,
        DecimalConditions(ProjectFairShareRow.normalized_usage),
        ColumnOrder(ProjectFairShareRow.normalized_usage),
    )
    total_decayed_usage = QueryColumn(ProjectFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = QueryColumn(ProjectFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = QueryColumn(
        ProjectFairShareRow.last_calculated_at,
        DateTimeConditions(ProjectFairShareRow.last_calculated_at),
        ColumnOrder(ProjectFairShareRow.last_calculated_at),
    )
    lookback_start = QueryColumn(
        ProjectFairShareRow.lookback_start,
        DateConditions(ProjectFairShareRow.lookback_start),
        ColumnOrder(ProjectFairShareRow.lookback_start),
    )
    lookback_end = QueryColumn(
        ProjectFairShareRow.lookback_end,
        DateConditions(ProjectFairShareRow.lookback_end),
        ColumnOrder(ProjectFairShareRow.lookback_end),
    )
    half_life_days = QueryColumn(
        ProjectFairShareRow.half_life_days,
        IntConditions(ProjectFairShareRow.half_life_days),
        ColumnOrder(ProjectFairShareRow.half_life_days),
    )
    lookback_days = QueryColumn(
        ProjectFairShareRow.lookback_days,
        IntConditions(ProjectFairShareRow.lookback_days),
        ColumnOrder(ProjectFairShareRow.lookback_days),
    )
    decay_unit_days = QueryColumn(
        ProjectFairShareRow.decay_unit_days,
        IntConditions(ProjectFairShareRow.decay_unit_days),
        ColumnOrder(ProjectFairShareRow.decay_unit_days),
    )
    created_at = QueryColumn(
        ProjectFairShareRow.created_at,
        DateTimeConditions(ProjectFairShareRow.created_at),
        ColumnOrder(ProjectFairShareRow.created_at),
    )
    updated_at = QueryColumn(
        ProjectFairShareRow.updated_at,
        DateTimeConditions(ProjectFairShareRow.updated_at),
        ColumnOrder(ProjectFairShareRow.updated_at),
    )


class ProjectFairShareQuerySpec:
    own = _ProjectFairShareOwnColumns()


class _UserFairShareOwnColumns:
    """The user fair share's own columns."""

    id = QueryColumn(
        UserFairShareRow.id,
        UUIDConditions(UserFairShareRow.id),
        ColumnOrder(UserFairShareRow.id),
    )
    resource_group = QueryColumn(
        UserFairShareRow.resource_group,
        StringConditions(UserFairShareRow.resource_group),
        ColumnOrder(UserFairShareRow.resource_group),
    )
    resource_group_id = QueryColumn(
        UserFairShareRow.resource_group_id,
        UUIDConditions(UserFairShareRow.resource_group_id),
        ColumnOrder(UserFairShareRow.resource_group_id),
    )
    user_uuid = QueryColumn(
        UserFairShareRow.user_uuid,
        UUIDConditions(UserFairShareRow.user_uuid),
        ColumnOrder(UserFairShareRow.user_uuid),
    )
    project_id = QueryColumn(
        UserFairShareRow.project_id,
        UUIDConditions(UserFairShareRow.project_id),
        ColumnOrder(UserFairShareRow.project_id),
    )
    domain_name = QueryColumn(
        UserFairShareRow.domain_name,
        StringConditions(UserFairShareRow.domain_name),
        ColumnOrder(UserFairShareRow.domain_name),
    )
    weight = QueryColumn(
        UserFairShareRow.weight,
        DecimalConditions(UserFairShareRow.weight),
        ColumnOrder(UserFairShareRow.weight),
    )
    fair_share_factor = QueryColumn(
        UserFairShareRow.fair_share_factor,
        DecimalConditions(UserFairShareRow.fair_share_factor),
        ColumnOrder(UserFairShareRow.fair_share_factor),
    )
    scheduling_rank = QueryColumn(
        UserFairShareRow.scheduling_rank,
        IntConditions(UserFairShareRow.scheduling_rank),
        ColumnOrder(UserFairShareRow.scheduling_rank),
    )
    normalized_usage = QueryColumn(
        UserFairShareRow.normalized_usage,
        DecimalConditions(UserFairShareRow.normalized_usage),
        ColumnOrder(UserFairShareRow.normalized_usage),
    )
    total_decayed_usage = QueryColumn(UserFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = QueryColumn(UserFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = QueryColumn(
        UserFairShareRow.last_calculated_at,
        DateTimeConditions(UserFairShareRow.last_calculated_at),
        ColumnOrder(UserFairShareRow.last_calculated_at),
    )
    lookback_start = QueryColumn(
        UserFairShareRow.lookback_start,
        DateConditions(UserFairShareRow.lookback_start),
        ColumnOrder(UserFairShareRow.lookback_start),
    )
    lookback_end = QueryColumn(
        UserFairShareRow.lookback_end,
        DateConditions(UserFairShareRow.lookback_end),
        ColumnOrder(UserFairShareRow.lookback_end),
    )
    half_life_days = QueryColumn(
        UserFairShareRow.half_life_days,
        IntConditions(UserFairShareRow.half_life_days),
        ColumnOrder(UserFairShareRow.half_life_days),
    )
    lookback_days = QueryColumn(
        UserFairShareRow.lookback_days,
        IntConditions(UserFairShareRow.lookback_days),
        ColumnOrder(UserFairShareRow.lookback_days),
    )
    decay_unit_days = QueryColumn(
        UserFairShareRow.decay_unit_days,
        IntConditions(UserFairShareRow.decay_unit_days),
        ColumnOrder(UserFairShareRow.decay_unit_days),
    )
    created_at = QueryColumn(
        UserFairShareRow.created_at,
        DateTimeConditions(UserFairShareRow.created_at),
        ColumnOrder(UserFairShareRow.created_at),
    )
    updated_at = QueryColumn(
        UserFairShareRow.updated_at,
        DateTimeConditions(UserFairShareRow.updated_at),
        ColumnOrder(UserFairShareRow.updated_at),
    )


class UserFairShareQuerySpec:
    own = _UserFairShareOwnColumns()
