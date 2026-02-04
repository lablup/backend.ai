"""User V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import override
from uuid import UUID

import strawberry

from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

from .enums import UserRoleEnum, UserStatusEnum


@strawberry.input(
    name="UserStatusV2EnumFilter",
    description=(
        "Added in 26.2.0. Filter for UserStatusEnum fields. "
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class UserStatusEnumFilter:
    """Filter for user status enum fields."""

    equals: UserStatusEnum | None = strawberry.field(
        default=None,
        description="Exact match for user status.",
    )
    in_: list[UserStatusEnum] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided statuses.",
    )
    not_equals: UserStatusEnum | None = strawberry.field(
        default=None,
        description="Exclude exact status match.",
    )
    not_in: list[UserStatusEnum] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided statuses.",
    )


@strawberry.input(
    name="UserRoleV2EnumFilter",
    description=(
        "Added in 26.2.0. Filter for UserRoleEnum fields. "
        "Supports equals, in, not_equals, and not_in operations."
    ),
)
class UserRoleEnumFilter:
    """Filter for user role enum fields."""

    equals: UserRoleEnum | None = strawberry.field(
        default=None,
        description="Exact match for user role.",
    )
    in_: list[UserRoleEnum] | None = strawberry.field(
        name="in",
        default=None,
        description="Match any of the provided roles.",
    )
    not_equals: UserRoleEnum | None = strawberry.field(
        default=None,
        description="Exclude exact role match.",
    )
    not_in: list[UserRoleEnum] | None = strawberry.field(
        default=None,
        description="Exclude any of the provided roles.",
    )


@strawberry.input(
    name="UserV2Filter",
    description=(
        "Added in 26.2.0. Filter input for querying users. "
        "Supports filtering by UUID, username, email, status, domain, role, and creation time. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class UserV2Filter(GQLFilter):
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
    status: UserStatusEnumFilter | None = strawberry.field(
        default=None,
        description="Filter by account status. Supports equals, in, not_equals, and not_in operations.",
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by domain name. Supports equals, contains, startsWith, and endsWith.",
    )
    role: UserRoleEnumFilter | None = strawberry.field(
        default=None,
        description="Filter by user role. Supports equals, in, not_equals, and not_in operations.",
    )
    created_at: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Filter by creation timestamp. Supports before, after, and between operations.",
    )

    AND: list[UserV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[UserV2Filter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[UserV2Filter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from filter fields.

        Returns:
            List of QueryCondition callables.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError("UserV2Filter.build_conditions is not yet implemented")


@strawberry.enum(
    name="UserV2OrderField",
    description=(
        "Added in 26.2.0. Fields available for ordering user query results. "
        "CREATED_AT: Order by creation timestamp. "
        "MODIFIED_AT: Order by last modification timestamp. "
        "USERNAME: Order by username alphabetically. "
        "EMAIL: Order by email address alphabetically. "
        "STATUS: Order by account status."
    ),
)
class UserV2OrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    STATUS = "status"


@strawberry.input(
    name="UserV2OrderBy",
    description=(
        "Added in 26.2.0. Specifies ordering for user query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class UserV2OrderBy(GQLOrderBy):
    """OrderBy for user queries."""

    field: UserV2OrderField = strawberry.field(
        description="The field to order by. See UserV2OrderField for available options."
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

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError("UserV2OrderBy.to_query_order is not yet implemented")


@strawberry.input(
    name="UserV2Scope",
    description=(
        "Added in 26.2.0. Scope for user queries to restrict results to a specific context."
    ),
)
class UserV2Scope:
    """Scope for user queries."""

    domain_name: str | None = strawberry.field(
        default=None,
        description="Restrict results to users in this domain.",
    )
    project_id: UUID | None = strawberry.field(
        default=None,
        description="Restrict results to users in this project.",
    )
