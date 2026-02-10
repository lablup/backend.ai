"""User GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import override
from uuid import UUID

import strawberry

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.domain.options import DomainConditions
from ai.backend.manager.repositories.group.options import GroupConditions
from ai.backend.manager.repositories.user.options import UserConditions, UserOrders

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@strawberry.input(
    name="UserDomainNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for the domain a user belongs to. "
        "Filters users whose domain matches all specified conditions."
    ),
)
class UserDomainNestedFilter:
    """Nested filter for domain of a user."""

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
        return [UserConditions.exists_domain_combined(raw_conditions)]


@strawberry.input(
    name="UserProjectNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for projects a user belongs to. "
        "Filters users that belong to at least one project matching all specified conditions."
    ),
)
class UserProjectNestedFilter:
    """Nested filter for projects of a user."""

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
        return [UserConditions.exists_project_combined(raw_conditions)]


@strawberry.input(
    name="UserStatusV2EnumFilter",
    description=(
        "Added in 26.2.0. Filter for UserStatusV2 enum fields."
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class UserStatusEnumFilterGQL:
    """Filter for user status enum fields."""

    equals: UserStatusEnumGQL | None = strawberry.field(
        default=None,
        description="Exact match for user status.",
    )
    in_: list[UserStatusEnumGQL] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided statuses.",
    )
    not_equals: UserStatusEnumGQL | None = strawberry.field(
        default=None,
        description="Exclude exact status match.",
    )
    not_in: list[UserStatusEnumGQL] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided statuses.",
    )


@strawberry.input(
    name="UserRoleV2EnumFilter",
    description=(
        "Added in 26.2.0. Filter for UserRoleV2 enum fields."
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class UserRoleEnumFilterGQL:
    """Filter for user role enum fields."""

    equals: UserRoleEnumGQL | None = strawberry.field(
        default=None,
        description="Exact match for user role.",
    )
    in_: list[UserRoleEnumGQL] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided roles.",
    )
    not_equals: UserRoleEnumGQL | None = strawberry.field(
        default=None,
        description="Exclude exact role match.",
    )
    not_in: list[UserRoleEnumGQL] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided roles.",
    )


@strawberry.input(
    name="UserV2Filter",
    description=(
        "Added in 26.2.0. Filter input for querying users. "
        "Supports filtering by UUID, username, email, status, domain, role, creation time, "
        "and nested domain/project filters. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class UserFilterGQL(GQLFilter):
    """Filter for user queries."""

    uuid: UUIDFilter | None = strawberry.field(
        default=None,
        description="Filter by user UUID. Supports equals and 'in' operations.",
    )
    username: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by username. Supports equals, contains, startsWith, and endsWith.",
    )
    email: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by email address. Supports equals, contains, startsWith, and endsWith.",
    )
    status: UserStatusEnumFilterGQL | None = strawberry.field(
        default=None,
        description="Filter by account status. Supports equals, in, not_equals, and not_in operations.",
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by domain name. Supports equals, contains, startsWith, and endsWith.",
    )
    role: UserRoleEnumFilterGQL | None = strawberry.field(
        default=None,
        description="Filter by user role. Supports equals, in, not_equals, and not_in operations.",
    )
    created_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by creation timestamp. Supports before, after, and between operations.",
    )
    domain: UserDomainNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested domain conditions. "
            "Returns users whose domain matches all specified conditions."
        ),
    )
    project: UserProjectNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by nested project conditions. "
            "Returns users that belong to at least one project matching all specified conditions."
        ),
    )

    AND: list[UserFilterGQL] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[UserFilterGQL] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[UserFilterGQL] | None = strawberry.field(
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

        if self.uuid:
            condition = self.uuid.build_query_condition(
                equals_factory=lambda spec: UserConditions.by_uuid_equals(spec),
                in_factory=lambda spec: UserConditions.by_uuid_in(spec),
            )
            if condition:
                conditions.append(condition)

        if self.username:
            condition = self.username.build_query_condition(
                contains_factory=lambda spec: UserConditions.by_username_contains(spec),
                equals_factory=lambda spec: UserConditions.by_username_equals(spec),
                starts_with_factory=lambda spec: UserConditions.by_username_starts_with(spec),
                ends_with_factory=lambda spec: UserConditions.by_username_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.email:
            condition = self.email.build_query_condition(
                contains_factory=lambda spec: UserConditions.by_email_contains(spec),
                equals_factory=lambda spec: UserConditions.by_email_equals(spec),
                starts_with_factory=lambda spec: UserConditions.by_email_starts_with(spec),
                ends_with_factory=lambda spec: UserConditions.by_email_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.status:
            if self.status.equals:
                conditions.append(
                    UserConditions.by_status_equals(UserStatus[self.status.equals.name])
                )
            if self.status.in_:
                conditions.append(
                    UserConditions.by_status_in([
                        UserStatus[status.name] for status in self.status.in_
                    ])
                )

        if self.domain_name:
            condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: UserConditions.by_domain_name_contains(spec),
                equals_factory=lambda spec: UserConditions.by_domain_name_equals(spec),
                starts_with_factory=lambda spec: UserConditions.by_domain_name_starts_with(spec),
                ends_with_factory=lambda spec: UserConditions.by_domain_name_ends_with(spec),
            )
            if condition:
                conditions.append(condition)

        if self.role:
            if self.role.equals:
                conditions.append(UserConditions.by_role_equals(UserRole[self.role.equals.name]))
            if self.role.in_:
                conditions.append(
                    UserConditions.by_role_in([UserRole[role.name] for role in self.role.in_])
                )

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=lambda dt: UserConditions.by_created_at_before(dt),
                after_factory=lambda dt: UserConditions.by_created_at_after(dt),
            )
            if condition:
                conditions.append(condition)

        if self.domain:
            conditions.extend(self.domain.build_conditions())

        if self.project:
            conditions.extend(self.project.build_conditions())

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
    name="UserV2OrderField",
    description=(
        "Added in 26.2.0. Fields available for ordering user query results. "
        "CREATED_AT: Order by creation timestamp. "
        "MODIFIED_AT: Order by last modification timestamp. "
        "USERNAME: Order by username alphabetically. "
        "EMAIL: Order by email address alphabetically. "
        "STATUS: Order by account status. "
        "DOMAIN_NAME: Order by domain name (scalar subquery). "
        "PROJECT_NAME: Order by project name (MIN aggregation)."
    ),
)
class UserOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    STATUS = "status"
    DOMAIN_NAME = "domain_name"
    PROJECT_NAME = "project_name"


@strawberry.input(
    name="UserV2OrderBy",
    description=(
        "Added in 26.2.0. Specifies ordering for user query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class UserOrderByGQL(GQLOrderBy):
    """OrderBy for user queries."""

    field: UserOrderFieldGQL = strawberry.field(
        description="The field to order by. See UserOrderField for available options."
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
            case UserOrderFieldGQL.CREATED_AT:
                return UserOrders.created_at(ascending)
            case UserOrderFieldGQL.MODIFIED_AT:
                return UserOrders.modified_at(ascending)
            case UserOrderFieldGQL.USERNAME:
                return UserOrders.username(ascending)
            case UserOrderFieldGQL.EMAIL:
                return UserOrders.email(ascending)
            case UserOrderFieldGQL.STATUS:
                return UserOrders.status(ascending)
            case UserOrderFieldGQL.DOMAIN_NAME:
                return UserOrders.by_domain_name(ascending)
            case UserOrderFieldGQL.PROJECT_NAME:
                return UserOrders.by_project_name(ascending)
            case _:
                raise ValueError(f"Unknown order field: {self.field}")


@strawberry.input(
    name="UserV2Scope",
    description=(
        "Added in 26.2.0. Scope for user queries to restrict results to a specific context."
    ),
)
class UserScopeGQL:
    """Scope for user queries."""

    domain_name: str | None = strawberry.field(
        default=None,
        description="Restrict results to users in this domain.",
    )
    project_id: UUID | None = strawberry.field(
        default=None,
        description="Restrict results to users in this project.",
    )
