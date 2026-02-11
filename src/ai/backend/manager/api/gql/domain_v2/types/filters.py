"""Domain V2 GraphQL filter and order-by types."""

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
from ai.backend.manager.repositories.domain.options import DomainConditions, DomainOrders
from ai.backend.manager.repositories.group.options import GroupConditions
from ai.backend.manager.repositories.user.options import UserConditions


@strawberry.input(
    name="DomainV2ProjectNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for projects belonging to a domain. "
        "Filters domains that have at least one project matching all specified conditions."
    ),
)
class DomainV2ProjectNestedFilter:
    """Nested filter for projects within a domain."""

    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by project name. Supports equals, contains, startsWith, and endsWith.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by project active status.",
    )

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions for project nested filter.

        Returns:
            List containing a single EXISTS condition wrapping all project sub-conditions,
            or empty list if no filters specified.
        """
        raw_conditions: list[QueryCondition] = []
        if self.name:
            condition = self.name.build_query_condition(
                contains_factory=lambda spec: GroupConditions.by_name_contains(spec),
                equals_factory=lambda spec: GroupConditions.by_name_equals(spec),
                starts_with_factory=lambda spec: GroupConditions.by_name_starts_with(spec),
                ends_with_factory=lambda spec: GroupConditions.by_name_ends_with(spec),
            )
            if condition:
                raw_conditions.append(condition)
        if self.is_active is not None:
            raw_conditions.append(GroupConditions.by_is_active(self.is_active))
        if not raw_conditions:
            return []
        return [DomainConditions.exists_project_combined(raw_conditions)]


@strawberry.input(
    name="DomainV2UserNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for users belonging to a domain. "
        "Filters domains that have at least one user matching all specified conditions."
    ),
)
class DomainV2UserNestedFilter:
    """Nested filter for users within a domain."""

    username: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by username. Supports equals, contains, startsWith, and endsWith.",
    )
    email: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by email. Supports equals, contains, startsWith, and endsWith.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by user active status. True for active users (status=ACTIVE), False for inactive.",
    )

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions for user nested filter.

        Returns:
            List containing a single EXISTS condition wrapping all user sub-conditions,
            or empty list if no filters specified.
        """
        raw_conditions: list[QueryCondition] = []
        if self.username:
            condition = self.username.build_query_condition(
                contains_factory=lambda spec: UserConditions.by_username_contains(spec),
                equals_factory=lambda spec: UserConditions.by_username_equals(spec),
                starts_with_factory=lambda spec: UserConditions.by_username_starts_with(spec),
                ends_with_factory=lambda spec: UserConditions.by_username_ends_with(spec),
            )
            if condition:
                raw_conditions.append(condition)
        if self.email:
            condition = self.email.build_query_condition(
                contains_factory=lambda spec: UserConditions.by_email_contains(spec),
                equals_factory=lambda spec: UserConditions.by_email_equals(spec),
                starts_with_factory=lambda spec: UserConditions.by_email_starts_with(spec),
                ends_with_factory=lambda spec: UserConditions.by_email_ends_with(spec),
            )
            if condition:
                raw_conditions.append(condition)
        if self.is_active is not None:
            raw_conditions.append(UserConditions.by_is_active(self.is_active))
        if not raw_conditions:
            return []
        return [DomainConditions.exists_user_combined(raw_conditions)]


@strawberry.input(
    name="DomainV2Filter",
    description=(
        "Added in 26.2.0. Filter input for querying domains. "
        "Supports filtering by name, description, active status, timestamps, "
        "and nested project/user filters. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class DomainV2Filter(GQLFilter):
    """Filter for domain queries."""

    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by domain name. Supports equals, contains, startsWith, and endsWith.",
    )
    description: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain description. Supports equals, contains, startsWith, and endsWith."
        ),
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by active status. True for active domains, False for inactive domains.",
    )
    created_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by creation timestamp. Supports before, after, and between operations.",
    )
    modified_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by last modification timestamp. Supports before, after, and between operations.",
    )
    project: DomainV2ProjectNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested project conditions. "
            "Returns domains that have at least one project matching all specified conditions."
        ),
    )
    user: DomainV2UserNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested user conditions. "
            "Returns domains that have at least one user matching all specified conditions."
        ),
    )

    AND: list[DomainV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[DomainV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[DomainV2Filter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from filter fields.

        Returns:
            List of QueryCondition callables.
        """
        conditions: list[QueryCondition] = []

        if self.name:
            condition = self.name.build_query_condition(
                contains_factory=lambda spec: DomainConditions.by_name_contains(spec),
                equals_factory=lambda spec: DomainConditions.by_name_equals(spec),
                starts_with_factory=lambda spec: DomainConditions.by_name_starts_with(spec),
                ends_with_factory=lambda spec: DomainConditions.by_name_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.description:
            condition = self.description.build_query_condition(
                contains_factory=lambda spec: DomainConditions.by_description_contains(spec),
                equals_factory=lambda spec: DomainConditions.by_description_equals(spec),
                starts_with_factory=lambda spec: DomainConditions.by_description_starts_with(spec),
                ends_with_factory=lambda spec: DomainConditions.by_description_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.is_active is not None:
            conditions.append(DomainConditions.by_is_active(self.is_active))

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=lambda dt: DomainConditions.by_created_at_before(dt),
                after_factory=lambda dt: DomainConditions.by_created_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.modified_at:
            condition = self.modified_at.build_query_condition(
                before_factory=lambda dt: DomainConditions.by_modified_at_before(dt),
                after_factory=lambda dt: DomainConditions.by_modified_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.project:
            conditions.extend(self.project.build_conditions())

        if self.user:
            conditions.extend(self.user.build_conditions())

        # Handle logical operators
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
    name="DomainV2OrderField",
    description=(
        "Added in 26.2.0. Fields available for ordering domain query results. "
        "CREATED_AT: Order by creation timestamp. "
        "MODIFIED_AT: Order by last modification timestamp. "
        "NAME: Order by domain name alphabetically. "
        "IS_ACTIVE: Order by active status. "
        "PROJECT_NAME: Order by project name (MIN aggregation). "
        "USER_USERNAME: Order by username (MIN aggregation). "
        "USER_EMAIL: Order by user email (MIN aggregation)."
    ),
)
class DomainV2OrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    NAME = "name"
    IS_ACTIVE = "is_active"
    PROJECT_NAME = "project_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


@strawberry.input(
    name="DomainV2OrderBy",
    description=(
        "Added in 26.2.0. Specifies ordering for domain query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class DomainV2OrderBy(GQLOrderBy):
    """OrderBy for domain queries."""

    field: DomainV2OrderField = strawberry.field(
        description="The field to order by. See DomainV2OrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description="Sort direction. ASC for ascending, DESC for descending.",
    )

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder.

        Returns:
            QueryOrder for the specified field and direction.
        """
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case DomainV2OrderField.CREATED_AT:
                return DomainOrders.created_at(ascending)
            case DomainV2OrderField.MODIFIED_AT:
                return DomainOrders.modified_at(ascending)
            case DomainV2OrderField.NAME:
                return DomainOrders.name(ascending)
            case DomainV2OrderField.IS_ACTIVE:
                return DomainOrders.is_active(ascending)
            case DomainV2OrderField.PROJECT_NAME:
                return DomainOrders.by_project_name(ascending)
            case DomainV2OrderField.USER_USERNAME:
                return DomainOrders.by_user_username(ascending)
            case DomainV2OrderField.USER_EMAIL:
                return DomainOrders.by_user_email(ascending)
