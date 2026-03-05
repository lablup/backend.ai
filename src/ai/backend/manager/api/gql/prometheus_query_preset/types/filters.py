"""Prometheus query preset GQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import override

import strawberry

from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.prometheus_query_preset.options import (
    PrometheusQueryPresetConditions,
    PrometheusQueryPresetOrders,
)


@strawberry.input(
    name="PrometheusQueryPresetFilter",
    description="Filter input for querying prometheus query presets.",
)
class PrometheusQueryPresetFilter(GQLFilter):
    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by preset name.",
    )
    metric_name: str | None = strawberry.field(
        default=None,
        description="Filter by exact metric name.",
    )
    created_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by creation timestamp.",
    )

    AND: list[PrometheusQueryPresetFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic.",
    )
    OR: list[PrometheusQueryPresetFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic.",
    )
    NOT: list[PrometheusQueryPresetFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.name:
            condition = self.name.build_query_condition(
                contains_factory=lambda spec: PrometheusQueryPresetConditions.by_name_contains(
                    spec
                ),
                equals_factory=lambda spec: PrometheusQueryPresetConditions.by_name_equals(spec),
                starts_with_factory=lambda spec: PrometheusQueryPresetConditions.by_name_starts_with(
                    spec
                ),
                ends_with_factory=lambda spec: PrometheusQueryPresetConditions.by_name_ends_with(
                    spec
                ),
            )
            if condition:
                conditions.append(condition)

        if self.metric_name is not None:
            conditions.append(
                PrometheusQueryPresetConditions.by_metric_name_equals(self.metric_name)
            )

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=lambda dt: PrometheusQueryPresetConditions.by_created_at_before(dt),
                after_factory=lambda dt: PrometheusQueryPresetConditions.by_created_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.AND:
            for sub_filter in self.AND:
                conditions.extend(sub_filter.build_conditions())

        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions


@strawberry.enum(
    name="PrometheusQueryPresetOrderField",
    description="Fields available for ordering prometheus query preset results.",
)
class PrometheusQueryPresetOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"


@strawberry.input(
    name="PrometheusQueryPresetOrderBy",
    description="Specifies ordering for prometheus query preset results.",
)
class PrometheusQueryPresetOrderBy(GQLOrderBy):
    field: PrometheusQueryPresetOrderField = strawberry.field(description="The field to order by.")
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description="Sort direction.",
    )

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case PrometheusQueryPresetOrderField.CREATED_AT:
                return PrometheusQueryPresetOrders.created_at(ascending)
            case PrometheusQueryPresetOrderField.UPDATED_AT:
                return PrometheusQueryPresetOrders.updated_at(ascending)
            case PrometheusQueryPresetOrderField.NAME:
                return PrometheusQueryPresetOrders.name(ascending)
