"""GraphQL types for resource group."""

from __future__ import annotations

from enum import StrEnum
from typing import Self, override

import strawberry
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.scaling_group.types import (
    ScalingGroupData,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)

__all__ = (
    "ResourceGroupFilterGQL",
    "ResourceGroupOrderByGQL",
    "ResourceGroupOrderFieldGQL",
    "ResourceGroupGQL",
)


@strawberry.type(
    name="ResourceGroup",
    description="Added in 26.1.0. Resource group with structured configuration",
)
class ResourceGroupGQL(Node):
    id: NodeID[str] = strawberry.field(
        description="Relay-style global node identifier for the resource group"
    )
    name: str = strawberry.field(
        description=dedent_strip("""
            Unique name identifying the resource group.
            Used as primary key and referenced by agents, sessions, and resource presets.
        """)
    )

    @classmethod
    def from_dataclass(cls, data: ScalingGroupData) -> Self:
        return cls(
            id=data.name,
            name=data.name,
        )


# Filter and OrderBy types


@strawberry.enum(
    name="ResourceGroupOrderField",
    description="Added in 26.1.0. Fields available for ordering resource groups",
)
class ResourceGroupOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"
    IS_PUBLIC = "is_public"


@strawberry.input(
    name="ResourceGroupFilter",
    description="Added in 26.1.0. Filter for resource groups",
)
class ResourceGroupFilterGQL(GQLFilter):
    name: StringFilter | None = None
    description: StringFilter | None = None
    is_active: bool | None = None
    is_public: bool | None = None
    scheduler: str | None = None
    use_host_network: bool | None = None

    AND: list[ResourceGroupFilterGQL] | None = None
    OR: list[ResourceGroupFilterGQL] | None = None
    NOT: list[ResourceGroupFilterGQL] | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing a single combined QueryCondition that represents
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=ScalingGroupConditions.by_name_contains,
                equals_factory=ScalingGroupConditions.by_name_equals,
                starts_with_factory=ScalingGroupConditions.by_name_starts_with,
                ends_with_factory=ScalingGroupConditions.by_name_ends_with,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply description filter
        if self.description:
            description_condition = self.description.build_query_condition(
                contains_factory=ScalingGroupConditions.by_description_contains,
                equals_factory=ScalingGroupConditions.by_description_equals,
                starts_with_factory=ScalingGroupConditions.by_description_starts_with,
                ends_with_factory=ScalingGroupConditions.by_description_ends_with,
            )
            if description_condition:
                field_conditions.append(description_condition)

        # Apply is_active filter
        if self.is_active is not None:
            field_conditions.append(ScalingGroupConditions.by_is_active(self.is_active))

        # Apply is_public filter
        if self.is_public is not None:
            field_conditions.append(ScalingGroupConditions.by_is_public(self.is_public))

        # Apply scheduler filter
        if self.scheduler:
            field_conditions.append(ScalingGroupConditions.by_scheduler(self.scheduler))

        # Apply use_host_network filter
        if self.use_host_network is not None:
            field_conditions.append(
                ScalingGroupConditions.by_use_host_network(self.use_host_network)
            )

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(
    name="ResourceGroupOrderBy",
    description="Added in 26.1.0. Order by specification for resource groups",
)
class ResourceGroupOrderByGQL(GQLOrderBy):
    field: ResourceGroupOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ResourceGroupOrderFieldGQL.NAME:
                return ScalingGroupOrders.name(ascending)
            case ResourceGroupOrderFieldGQL.CREATED_AT:
                return ScalingGroupOrders.created_at(ascending)
            case ResourceGroupOrderFieldGQL.IS_ACTIVE:
                return ScalingGroupOrders.is_active(ascending)
            case ResourceGroupOrderFieldGQL.IS_PUBLIC:
                return ScalingGroupOrders.is_public(ascending)
