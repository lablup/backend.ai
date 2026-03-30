"""User GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.user.request import UserFilter, UserOrder
from ai.backend.common.dto.manager.v2.user.types import (
    UserDomainFilter,
    UserProjectFilter,
    UserRoleFilter,
    UserStatusFilter,
)
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserStatusV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="UserStatusV2EnumFilter",
)
class UserStatusEnumFilterGQL(PydanticInputMixin[UserStatusFilter]):
    """Filter for user status enum fields."""

    equals: UserStatusEnumGQL | None = None
    in_: list[UserStatusEnumGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: UserStatusEnumGQL | None = None
    not_in: list[UserStatusEnumGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserRoleV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="UserRoleV2EnumFilter",
)
class UserRoleEnumFilterGQL(PydanticInputMixin[UserRoleFilter]):
    """Filter for user role enum fields."""

    equals: UserRoleEnumGQL | None = None
    in_: list[UserRoleEnumGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: UserRoleEnumGQL | None = None
    not_in: list[UserRoleEnumGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for the domain a user belongs to. Filters users whose domain matches all specified conditions.",
        added_version="26.2.0",
    ),
    name="UserDomainNestedFilter",
)
class UserDomainNestedFilterGQL(PydanticInputMixin[UserDomainFilter]):
    """Nested filter for domain of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for projects a user belongs to. Filters users that belong to at least one project matching all specified conditions.",
        added_version="26.2.0",
    ),
    name="UserProjectNestedFilter",
)
class UserProjectNestedFilterGQL(PydanticInputMixin[UserProjectFilter]):
    """Nested filter for projects of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying users. Supports filtering by UUID, username, email, status, domain, integration_name, role, creation time, and nested domain/project filters. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.2.0",
    ),
    name="UserV2Filter",
)
class UserFilterGQL(PydanticInputMixin[UserFilter]):
    """Filter for user queries."""

    uuid: UUIDFilter | None = None
    username: StringFilter | None = None
    email: StringFilter | None = None
    status: UserStatusEnumFilterGQL | None = None
    domain_name: StringFilter | None = None
    integration_name: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by external integration identifier.",
        ),
        default=None,
    )
    role: UserRoleEnumFilterGQL | None = None
    created_at: DateTimeFilter | None = None
    domain: UserDomainNestedFilterGQL | None = None
    project: UserProjectNestedFilterGQL | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Fields available for ordering user query results. "
            "CREATED_AT: Order by creation timestamp. "
            "MODIFIED_AT: Order by last modification timestamp. "
            "USERNAME: Order by username alphabetically. "
            "EMAIL: Order by email address alphabetically. "
            "STATUS: Order by account status. "
            "DOMAIN_NAME: Order by domain name (scalar subquery). "
            "PROJECT_NAME: Order by project name (MIN aggregation)."
        ),
    ),
    name="UserV2OrderField",
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
    name="UserV2OrderBy",
)
class UserOrderByGQL(PydanticInputMixin[UserOrder]):
    """OrderBy for user queries."""

    field: UserOrderFieldGQL = UserOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
