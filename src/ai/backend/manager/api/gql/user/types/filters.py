"""User GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

import strawberry

from ai.backend.common.dto.manager.v2.user.request import UserFilter, UserOrder
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserDomainFilter,
    UserOrderField,
    UserProjectFilter,
    UserRoleFilter,
    UserStatusFilter,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserStatusV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    model=UserStatusFilter,
    name="UserStatusV2EnumFilter",
)
class UserStatusEnumFilterGQL:
    """Filter for user status enum fields."""

    equals: UserStatusEnumGQL | None = None
    in_: list[UserStatusEnumGQL] | None = strawberry.field(name="in", default=None)
    not_equals: UserStatusEnumGQL | None = None
    not_in: list[UserStatusEnumGQL] | None = None

    def to_pydantic(self) -> UserStatusFilter:
        from ai.backend.common.dto.manager.v2.user.types import UserStatus as UserStatusDTO

        return UserStatusFilter(
            equals=UserStatusDTO(self.equals.value) if self.equals else None,
            in_=[UserStatusDTO(s.value) for s in self.in_] if self.in_ else None,
            not_equals=UserStatusDTO(self.not_equals.value) if self.not_equals else None,
            not_in=[UserStatusDTO(s.value) for s in self.not_in] if self.not_in else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserRoleV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    model=UserRoleFilter,
    name="UserRoleV2EnumFilter",
)
class UserRoleEnumFilterGQL:
    """Filter for user role enum fields."""

    equals: UserRoleEnumGQL | None = None
    in_: list[UserRoleEnumGQL] | None = strawberry.field(name="in", default=None)
    not_equals: UserRoleEnumGQL | None = None
    not_in: list[UserRoleEnumGQL] | None = None

    def to_pydantic(self) -> UserRoleFilter:
        from ai.backend.common.dto.manager.v2.user.types import UserRole as UserRoleDTO

        return UserRoleFilter(
            equals=UserRoleDTO(self.equals.value) if self.equals else None,
            in_=[UserRoleDTO(r.value) for r in self.in_] if self.in_ else None,
            not_equals=UserRoleDTO(self.not_equals.value) if self.not_equals else None,
            not_in=[UserRoleDTO(r.value) for r in self.not_in] if self.not_in else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for the domain a user belongs to. Filters users whose domain matches all specified conditions.",
        added_version="26.2.0",
    ),
    model=UserDomainFilter,
    name="UserDomainNestedFilter",
)
class UserDomainNestedFilterGQL:
    """Nested filter for domain of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> UserDomainFilter:
        return UserDomainFilter(
            name=self.name.to_pydantic() if self.name else None,
            is_active=self.is_active,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for projects a user belongs to. Filters users that belong to at least one project matching all specified conditions.",
        added_version="26.2.0",
    ),
    model=UserProjectFilter,
    name="UserProjectNestedFilter",
)
class UserProjectNestedFilterGQL:
    """Nested filter for projects of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> UserProjectFilter:
        return UserProjectFilter(
            name=self.name.to_pydantic() if self.name else None,
            is_active=self.is_active,
        )


@strawberry.input(
    name="UserV2Filter",
    description="Added in 26.2.0. Filter input for querying users. Supports filtering by UUID, username, email, status, domain, role, creation time, and nested domain/project filters. Multiple filters can be combined using AND, OR, and NOT logical operators.",
)
class UserFilterGQL:
    """Filter for user queries."""

    uuid: UUIDFilter | None = None
    username: StringFilter | None = None
    email: StringFilter | None = None
    status: UserStatusEnumFilterGQL | None = None
    domain_name: StringFilter | None = None
    role: UserRoleEnumFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    domain: UserDomainNestedFilterGQL | None = None
    project: UserProjectNestedFilterGQL | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> UserFilter:
        return UserFilter(
            uuid=self.uuid.to_pydantic() if self.uuid else None,
            username=self.username.to_pydantic() if self.username else None,
            email=self.email.to_pydantic() if self.email else None,
            status=self.status.to_pydantic() if self.status else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            role=self.role.to_pydantic() if self.role else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            domain=self.domain.to_pydantic() if self.domain else None,
            project=self.project.to_pydantic() if self.project else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for user query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.2.0",
    ),
    model=UserOrder,
    name="UserV2OrderBy",
)
class UserOrderByGQL:
    """OrderBy for user queries."""

    field: UserOrderFieldGQL = UserOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> UserOrder:
        direction = (
            OrderDirectionDTO.ASC
            if self.direction == OrderDirection.ASC
            else OrderDirectionDTO.DESC
        )
        match self.field:
            case UserOrderFieldGQL.CREATED_AT:
                return UserOrder(field=UserOrderField.CREATED_AT, direction=direction)
            case UserOrderFieldGQL.MODIFIED_AT:
                return UserOrder(field=UserOrderField.MODIFIED_AT, direction=direction)
            case UserOrderFieldGQL.USERNAME:
                return UserOrder(field=UserOrderField.USERNAME, direction=direction)
            case UserOrderFieldGQL.EMAIL:
                return UserOrder(field=UserOrderField.EMAIL, direction=direction)
            case UserOrderFieldGQL.STATUS:
                return UserOrder(field=UserOrderField.STATUS, direction=direction)
            case UserOrderFieldGQL.DOMAIN_NAME:
                return UserOrder(field=UserOrderField.DOMAIN_NAME, direction=direction)
            case UserOrderFieldGQL.PROJECT_NAME:
                return UserOrder(field=UserOrderField.PROJECT_NAME, direction=direction)
