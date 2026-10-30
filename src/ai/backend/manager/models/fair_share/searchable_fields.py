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
from ai.backend.manager.models.specs.search.field import SearchableField


class _DomainFairShareOwnFields:
    """The domain fair share's own columns."""

    id = SearchableField(
        DomainFairShareRow.id,
        UUIDConditions(DomainFairShareRow.id),
        ColumnOrder(DomainFairShareRow.id),
    )
    resource_group = SearchableField(
        DomainFairShareRow.resource_group,
        StringConditions(DomainFairShareRow.resource_group),
        ColumnOrder(DomainFairShareRow.resource_group),
    )
    resource_group_id = SearchableField(
        DomainFairShareRow.resource_group_id,
        UUIDConditions(DomainFairShareRow.resource_group_id),
        ColumnOrder(DomainFairShareRow.resource_group_id),
    )
    domain_name = SearchableField(
        DomainFairShareRow.domain_name,
        StringConditions(DomainFairShareRow.domain_name),
        ColumnOrder(DomainFairShareRow.domain_name),
    )
    weight = SearchableField(
        DomainFairShareRow.weight,
        DecimalConditions(DomainFairShareRow.weight),
        ColumnOrder(DomainFairShareRow.weight),
    )
    fair_share_factor = SearchableField(
        DomainFairShareRow.fair_share_factor,
        DecimalConditions(DomainFairShareRow.fair_share_factor),
        ColumnOrder(DomainFairShareRow.fair_share_factor),
    )
    normalized_usage = SearchableField(
        DomainFairShareRow.normalized_usage,
        DecimalConditions(DomainFairShareRow.normalized_usage),
        ColumnOrder(DomainFairShareRow.normalized_usage),
    )
    total_decayed_usage = SearchableField(DomainFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = SearchableField(DomainFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = SearchableField(
        DomainFairShareRow.last_calculated_at,
        DateTimeConditions(DomainFairShareRow.last_calculated_at),
        ColumnOrder(DomainFairShareRow.last_calculated_at),
    )
    lookback_start = SearchableField(
        DomainFairShareRow.lookback_start,
        DateConditions(DomainFairShareRow.lookback_start),
        ColumnOrder(DomainFairShareRow.lookback_start),
    )
    lookback_end = SearchableField(
        DomainFairShareRow.lookback_end,
        DateConditions(DomainFairShareRow.lookback_end),
        ColumnOrder(DomainFairShareRow.lookback_end),
    )
    half_life_days = SearchableField(
        DomainFairShareRow.half_life_days,
        IntConditions(DomainFairShareRow.half_life_days),
        ColumnOrder(DomainFairShareRow.half_life_days),
    )
    lookback_days = SearchableField(
        DomainFairShareRow.lookback_days,
        IntConditions(DomainFairShareRow.lookback_days),
        ColumnOrder(DomainFairShareRow.lookback_days),
    )
    decay_unit_days = SearchableField(
        DomainFairShareRow.decay_unit_days,
        IntConditions(DomainFairShareRow.decay_unit_days),
        ColumnOrder(DomainFairShareRow.decay_unit_days),
    )
    created_at = SearchableField(
        DomainFairShareRow.created_at,
        DateTimeConditions(DomainFairShareRow.created_at),
        ColumnOrder(DomainFairShareRow.created_at),
    )
    updated_at = SearchableField(
        DomainFairShareRow.updated_at,
        DateTimeConditions(DomainFairShareRow.updated_at),
        ColumnOrder(DomainFairShareRow.updated_at),
    )


class DomainFairShareSearchableFields:
    own = _DomainFairShareOwnFields()


class _ProjectFairShareOwnFields:
    """The project fair share's own columns."""

    id = SearchableField(
        ProjectFairShareRow.id,
        UUIDConditions(ProjectFairShareRow.id),
        ColumnOrder(ProjectFairShareRow.id),
    )
    resource_group = SearchableField(
        ProjectFairShareRow.resource_group,
        StringConditions(ProjectFairShareRow.resource_group),
        ColumnOrder(ProjectFairShareRow.resource_group),
    )
    resource_group_id = SearchableField(
        ProjectFairShareRow.resource_group_id,
        UUIDConditions(ProjectFairShareRow.resource_group_id),
        ColumnOrder(ProjectFairShareRow.resource_group_id),
    )
    project_id = SearchableField(
        ProjectFairShareRow.project_id,
        UUIDConditions(ProjectFairShareRow.project_id),
        ColumnOrder(ProjectFairShareRow.project_id),
    )
    domain_name = SearchableField(
        ProjectFairShareRow.domain_name,
        StringConditions(ProjectFairShareRow.domain_name),
        ColumnOrder(ProjectFairShareRow.domain_name),
    )
    weight = SearchableField(
        ProjectFairShareRow.weight,
        DecimalConditions(ProjectFairShareRow.weight),
        ColumnOrder(ProjectFairShareRow.weight),
    )
    fair_share_factor = SearchableField(
        ProjectFairShareRow.fair_share_factor,
        DecimalConditions(ProjectFairShareRow.fair_share_factor),
        ColumnOrder(ProjectFairShareRow.fair_share_factor),
    )
    normalized_usage = SearchableField(
        ProjectFairShareRow.normalized_usage,
        DecimalConditions(ProjectFairShareRow.normalized_usage),
        ColumnOrder(ProjectFairShareRow.normalized_usage),
    )
    total_decayed_usage = SearchableField(ProjectFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = SearchableField(ProjectFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = SearchableField(
        ProjectFairShareRow.last_calculated_at,
        DateTimeConditions(ProjectFairShareRow.last_calculated_at),
        ColumnOrder(ProjectFairShareRow.last_calculated_at),
    )
    lookback_start = SearchableField(
        ProjectFairShareRow.lookback_start,
        DateConditions(ProjectFairShareRow.lookback_start),
        ColumnOrder(ProjectFairShareRow.lookback_start),
    )
    lookback_end = SearchableField(
        ProjectFairShareRow.lookback_end,
        DateConditions(ProjectFairShareRow.lookback_end),
        ColumnOrder(ProjectFairShareRow.lookback_end),
    )
    half_life_days = SearchableField(
        ProjectFairShareRow.half_life_days,
        IntConditions(ProjectFairShareRow.half_life_days),
        ColumnOrder(ProjectFairShareRow.half_life_days),
    )
    lookback_days = SearchableField(
        ProjectFairShareRow.lookback_days,
        IntConditions(ProjectFairShareRow.lookback_days),
        ColumnOrder(ProjectFairShareRow.lookback_days),
    )
    decay_unit_days = SearchableField(
        ProjectFairShareRow.decay_unit_days,
        IntConditions(ProjectFairShareRow.decay_unit_days),
        ColumnOrder(ProjectFairShareRow.decay_unit_days),
    )
    created_at = SearchableField(
        ProjectFairShareRow.created_at,
        DateTimeConditions(ProjectFairShareRow.created_at),
        ColumnOrder(ProjectFairShareRow.created_at),
    )
    updated_at = SearchableField(
        ProjectFairShareRow.updated_at,
        DateTimeConditions(ProjectFairShareRow.updated_at),
        ColumnOrder(ProjectFairShareRow.updated_at),
    )


class ProjectFairShareSearchableFields:
    own = _ProjectFairShareOwnFields()


class _UserFairShareOwnFields:
    """The user fair share's own columns."""

    id = SearchableField(
        UserFairShareRow.id,
        UUIDConditions(UserFairShareRow.id),
        ColumnOrder(UserFairShareRow.id),
    )
    resource_group = SearchableField(
        UserFairShareRow.resource_group,
        StringConditions(UserFairShareRow.resource_group),
        ColumnOrder(UserFairShareRow.resource_group),
    )
    resource_group_id = SearchableField(
        UserFairShareRow.resource_group_id,
        UUIDConditions(UserFairShareRow.resource_group_id),
        ColumnOrder(UserFairShareRow.resource_group_id),
    )
    user_uuid = SearchableField(
        UserFairShareRow.user_uuid,
        UUIDConditions(UserFairShareRow.user_uuid),
        ColumnOrder(UserFairShareRow.user_uuid),
    )
    project_id = SearchableField(
        UserFairShareRow.project_id,
        UUIDConditions(UserFairShareRow.project_id),
        ColumnOrder(UserFairShareRow.project_id),
    )
    domain_name = SearchableField(
        UserFairShareRow.domain_name,
        StringConditions(UserFairShareRow.domain_name),
        ColumnOrder(UserFairShareRow.domain_name),
    )
    weight = SearchableField(
        UserFairShareRow.weight,
        DecimalConditions(UserFairShareRow.weight),
        ColumnOrder(UserFairShareRow.weight),
    )
    fair_share_factor = SearchableField(
        UserFairShareRow.fair_share_factor,
        DecimalConditions(UserFairShareRow.fair_share_factor),
        ColumnOrder(UserFairShareRow.fair_share_factor),
    )
    scheduling_rank = SearchableField(
        UserFairShareRow.scheduling_rank,
        IntConditions(UserFairShareRow.scheduling_rank),
        ColumnOrder(UserFairShareRow.scheduling_rank),
    )
    normalized_usage = SearchableField(
        UserFairShareRow.normalized_usage,
        DecimalConditions(UserFairShareRow.normalized_usage),
        ColumnOrder(UserFairShareRow.normalized_usage),
    )
    total_decayed_usage = SearchableField(UserFairShareRow.total_decayed_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    resource_weights = SearchableField(UserFairShareRow.resource_weights, None, None)
    """Impossible: a JSONB document of slot names to weights."""
    last_calculated_at = SearchableField(
        UserFairShareRow.last_calculated_at,
        DateTimeConditions(UserFairShareRow.last_calculated_at),
        ColumnOrder(UserFairShareRow.last_calculated_at),
    )
    lookback_start = SearchableField(
        UserFairShareRow.lookback_start,
        DateConditions(UserFairShareRow.lookback_start),
        ColumnOrder(UserFairShareRow.lookback_start),
    )
    lookback_end = SearchableField(
        UserFairShareRow.lookback_end,
        DateConditions(UserFairShareRow.lookback_end),
        ColumnOrder(UserFairShareRow.lookback_end),
    )
    half_life_days = SearchableField(
        UserFairShareRow.half_life_days,
        IntConditions(UserFairShareRow.half_life_days),
        ColumnOrder(UserFairShareRow.half_life_days),
    )
    lookback_days = SearchableField(
        UserFairShareRow.lookback_days,
        IntConditions(UserFairShareRow.lookback_days),
        ColumnOrder(UserFairShareRow.lookback_days),
    )
    decay_unit_days = SearchableField(
        UserFairShareRow.decay_unit_days,
        IntConditions(UserFairShareRow.decay_unit_days),
        ColumnOrder(UserFairShareRow.decay_unit_days),
    )
    created_at = SearchableField(
        UserFairShareRow.created_at,
        DateTimeConditions(UserFairShareRow.created_at),
        ColumnOrder(UserFairShareRow.created_at),
    )
    updated_at = SearchableField(
        UserFairShareRow.updated_at,
        DateTimeConditions(UserFairShareRow.updated_at),
        ColumnOrder(UserFairShareRow.updated_at),
    )


class UserFairShareSearchableFields:
    own = _UserFairShareOwnFields()
