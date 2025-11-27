"""GraphQL types for scaling group."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional, Self

import strawberry
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import JSONString, OrderDirection, StringFilter
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
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
    "ScalingGroup",
    "ScalingGroupFilter",
    "ScalingGroupOrderBy",
    "ScalingGroupOrderField",
)


@strawberry.type
class ScalingGroup(Node):
    id: NodeID[str]
    name: str
    description: str
    is_active: bool
    is_public: bool
    created_at: datetime
    wsproxy_addr: str
    wsproxy_api_token: str
    driver: str
    driver_opts: JSONString
    scheduler: str
    scheduler_opts: JSONString
    use_host_network: bool

    @classmethod
    def from_dataclass(cls, data: ScalingGroupData) -> Self:
        return cls(
            id=data.name,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            is_public=data.is_public,
            created_at=data.created_at,
            wsproxy_addr=data.wsproxy_addr,
            wsproxy_api_token=data.wsproxy_api_token,
            driver=data.driver,
            driver_opts=data.driver_opts,
            scheduler=data.scheduler,
            scheduler_opts=data.scheduler_opts,
            use_host_network=data.use_host_network,
        )


# Filter and OrderBy types


@strawberry.enum
class ScalingGroupOrderField(StrEnum):
    NAME = "name"
    DESCRIPTION = "description"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"
    IS_PUBLIC = "is_public"


@strawberry.input(description="Filter for scaling groups")
class ScalingGroupFilter:
    name: Optional[StringFilter] = None
    description: Optional[StringFilter] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    driver: Optional[str] = None
    scheduler: Optional[str] = None
    use_host_network: Optional[bool] = None

    AND: Optional[list[ScalingGroupFilter]] = None
    OR: Optional[list[ScalingGroupFilter]] = None
    NOT: Optional[list[ScalingGroupFilter]] = None

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
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply description filter
        if self.description:
            description_condition = self.description.build_query_condition(
                contains_factory=ScalingGroupConditions.by_description_contains,
                equals_factory=ScalingGroupConditions.by_description_equals,
            )
            if description_condition:
                field_conditions.append(description_condition)

        # Apply is_active filter
        if self.is_active is not None:
            field_conditions.append(ScalingGroupConditions.by_is_active(self.is_active))

        # Apply is_public filter
        if self.is_public is not None:
            field_conditions.append(ScalingGroupConditions.by_is_public(self.is_public))

        # Apply driver filter
        if self.driver:
            field_conditions.append(ScalingGroupConditions.by_driver(self.driver))

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


@strawberry.input(description="Order by specification for scaling groups")
class ScalingGroupOrderBy:
    field: ScalingGroupOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ScalingGroupOrderField.NAME:
                return ScalingGroupOrders.name(ascending)
            case ScalingGroupOrderField.DESCRIPTION:
                return ScalingGroupOrders.description(ascending)
            case ScalingGroupOrderField.CREATED_AT:
                return ScalingGroupOrders.created_at(ascending)
            case ScalingGroupOrderField.IS_ACTIVE:
                return ScalingGroupOrders.is_active(ascending)
            case ScalingGroupOrderField.IS_PUBLIC:
                return ScalingGroupOrders.is_public(ascending)
