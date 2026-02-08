"""Project V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import override

import strawberry

from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.domain.options import DomainConditions
from ai.backend.manager.repositories.group.options import GroupConditions, GroupOrders
from ai.backend.manager.repositories.user.options import UserConditions

from .enums import ProjectTypeEnum


@strawberry.input(
    name="ProjectDomainNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for the domain a project belongs to. "
        "Filters projects whose domain matches all specified conditions."
    ),
)
class ProjectDomainNestedFilter:
    """Nested filter for domain of a project."""

    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by domain name. Supports equals, contains, startsWith, and endsWith.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by domain active status.",
    )

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions for domain nested filter.

        Returns:
            List containing a single EXISTS condition wrapping all domain sub-conditions,
            or empty list if no filters specified.
        """
        raw_conditions: list[QueryCondition] = []
        if self.name:
            condition = self.name.build_query_condition(
                contains_factory=lambda spec: DomainConditions.by_name_contains(spec),
                equals_factory=lambda spec: DomainConditions.by_name_equals(spec),
                starts_with_factory=lambda spec: DomainConditions.by_name_starts_with(spec),
                ends_with_factory=lambda spec: DomainConditions.by_name_ends_with(spec),
            )
            if condition:
                raw_conditions.append(condition)
        if self.is_active is not None:
            raw_conditions.append(DomainConditions.by_is_active(self.is_active))
        if not raw_conditions:
            return []
        return [GroupConditions.exists_domain_combined(raw_conditions)]


@strawberry.input(
    name="ProjectUserNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for users belonging to a project. "
        "Filters projects that have at least one user matching all specified conditions."
    ),
)
class ProjectUserNestedFilter:
    """Nested filter for users within a project."""

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
        return [GroupConditions.exists_user_combined(raw_conditions)]


@strawberry.input(
    name="ProjectTypeV2EnumFilter",
    description=(
        "Added in 26.2.0. Filter for ProjectTypeEnum fields. "
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class ProjectTypeEnumFilter:
    """Filter for project type enum fields."""

    equals: ProjectTypeEnum | None = strawberry.field(
        default=None,
        description="Exact match for project type.",
    )
    in_: list[ProjectTypeEnum] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided types.",
    )
    not_equals: ProjectTypeEnum | None = strawberry.field(
        default=None,
        description="Exclude exact type match.",
    )
    not_in: list[ProjectTypeEnum] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided types.",
    )


@strawberry.input(
    name="ProjectV2Filter",
    description=(
        "Added in 26.2.0. Filter input for querying projects. "
        "Supports filtering by ID, name, domain, type, active status, and timestamps. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class ProjectV2Filter(GQLFilter):
    """Filter for project queries."""

    id: UUIDFilter | None = strawberry.field(
        default=None,
        description="Filter by project ID (UUID). Supports equals and 'in' operations.",
    )
    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by project name. Supports equals, contains, startsWith, and endsWith.",
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by domain name. Supports equals, contains, startsWith, and endsWith.",
    )
    type: ProjectTypeEnumFilter | None = strawberry.field(
        default=None,
        description="Filter by project type. Supports equals, in, not_equals, and not_in operations.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by active status. True for active projects, False for inactive projects.",
    )
    created_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by creation timestamp. Supports before, after, and between operations.",
    )
    modified_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by last modification timestamp. Supports before, after, and between operations.",
    )
    domain: ProjectDomainNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested domain conditions. "
            "Returns projects whose domain matches all specified conditions."
        ),
    )
    user: ProjectUserNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested user conditions. "
            "Returns projects that have at least one user matching all specified conditions."
        ),
    )

    AND: list[ProjectV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[ProjectV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[ProjectV2Filter] | None = strawberry.field(
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

        if self.id:
            condition = self.id.build_query_condition(
                equals_factory=lambda spec: GroupConditions.by_id_equals(spec),
                in_factory=lambda spec: GroupConditions.by_id_in(spec),
            )
            if condition:
                conditions.append(condition)

        if self.name:
            condition = self.name.build_query_condition(
                contains_factory=lambda spec: GroupConditions.by_name_contains(spec),
                equals_factory=lambda spec: GroupConditions.by_name_equals(spec),
                starts_with_factory=lambda spec: GroupConditions.by_name_starts_with(spec),
                ends_with_factory=lambda spec: GroupConditions.by_name_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.domain_name:
            condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: GroupConditions.by_domain_name_contains(spec),
                equals_factory=lambda spec: GroupConditions.by_domain_name_equals(spec),
                starts_with_factory=lambda spec: GroupConditions.by_domain_name_starts_with(spec),
                ends_with_factory=lambda spec: GroupConditions.by_domain_name_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.type:
            if self.type.equals:
                conditions.append(
                    GroupConditions.by_type_equals(ProjectType[self.type.equals.name])
                )
            if self.type.in_:
                conditions.append(
                    GroupConditions.by_type_in([
                        ProjectType[project_type.name] for project_type in self.type.in_
                    ])
                )

        if self.is_active is not None:
            conditions.append(GroupConditions.by_is_active(self.is_active))

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=lambda dt: GroupConditions.by_created_at_before(dt),
                after_factory=lambda dt: GroupConditions.by_created_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.modified_at:
            condition = self.modified_at.build_query_condition(
                before_factory=lambda dt: GroupConditions.by_modified_at_before(dt),
                after_factory=lambda dt: GroupConditions.by_modified_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.domain:
            conditions.extend(self.domain.build_conditions())

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
    name="ProjectV2OrderField",
    description=(
        "Added in 26.2.0. Fields available for ordering project query results. "
        "CREATED_AT: Order by creation timestamp. "
        "MODIFIED_AT: Order by last modification timestamp. "
        "NAME: Order by project name alphabetically. "
        "IS_ACTIVE: Order by active status. "
        "TYPE: Order by project type. "
        "DOMAIN_NAME: Order by domain name (scalar subquery). "
        "USER_USERNAME: Order by username (MIN aggregation). "
        "USER_EMAIL: Order by user email (MIN aggregation)."
    ),
)
class ProjectV2OrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    NAME = "name"
    IS_ACTIVE = "is_active"
    TYPE = "type"
    DOMAIN_NAME = "domain_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


@strawberry.input(
    name="ProjectV2OrderBy",
    description=(
        "Added in 26.2.0. Specifies ordering for project query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class ProjectV2OrderBy(GQLOrderBy):
    """OrderBy for project queries."""

    field: ProjectV2OrderField = strawberry.field(
        description="The field to order by. See ProjectV2OrderField for available options."
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
            case ProjectV2OrderField.CREATED_AT:
                return GroupOrders.created_at(ascending)
            case ProjectV2OrderField.MODIFIED_AT:
                return GroupOrders.modified_at(ascending)
            case ProjectV2OrderField.NAME:
                return GroupOrders.name(ascending)
            case ProjectV2OrderField.IS_ACTIVE:
                return GroupOrders.is_active(ascending)
            case ProjectV2OrderField.TYPE:
                return GroupOrders.type(ascending)
            case ProjectV2OrderField.DOMAIN_NAME:
                return GroupOrders.by_domain_name(ascending)
            case ProjectV2OrderField.USER_USERNAME:
                return GroupOrders.by_user_username(ascending)
            case ProjectV2OrderField.USER_EMAIL:
                return GroupOrders.by_user_email(ascending)
