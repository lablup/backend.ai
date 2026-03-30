"""Domain V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.domain.request import DomainFilter, DomainOrder
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainProjectFilter,
    DomainUserFilter,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for projects belonging to a domain. Filters domains that have at least one project matching all specified conditions.",
        added_version="26.2.0",
    ),
    name="DomainProjectNestedFilter",
)
class DomainProjectNestedFilter(PydanticInputMixin[DomainProjectFilter]):
    """Nested filter for projects within a domain."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for users belonging to a domain. Filters domains that have at least one user matching all specified conditions.",
        added_version="26.2.0",
    ),
    name="DomainUserNestedFilter",
)
class DomainUserNestedFilter(PydanticInputMixin[DomainUserFilter]):
    """Nested filter for users within a domain."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying domains. Supports filtering by name, description, active status, timestamps, and nested project/user filters. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.2.0",
    ),
    name="DomainV2Filter",
)
class DomainV2Filter(PydanticInputMixin[DomainFilter]):
    """Filter for domain queries."""

    name: StringFilter | None = None
    description: StringFilter | None = None
    is_active: bool | None = None
    created_at: DateTimeFilter | None = None
    modified_at: DateTimeFilter | None = None
    project: DomainProjectNestedFilter | None = None
    user: DomainUserNestedFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Fields available for ordering domain query results. "
            "CREATED_AT: Order by creation timestamp. "
            "MODIFIED_AT: Order by last modification timestamp. "
            "NAME: Order by domain name alphabetically. "
            "IS_ACTIVE: Order by active status. "
            "PROJECT_NAME: Order by project name (MIN aggregation). "
            "USER_USERNAME: Order by username (MIN aggregation). "
            "USER_EMAIL: Order by user email (MIN aggregation)."
        ),
    ),
    name="DomainV2OrderField",
)
class DomainV2OrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    NAME = "name"
    IS_ACTIVE = "is_active"
    PROJECT_NAME = "project_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for domain query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.2.0",
    ),
    name="DomainV2OrderBy",
)
class DomainV2OrderBy(PydanticInputMixin[DomainOrder]):
    """OrderBy for domain queries."""

    field: DomainV2OrderField = DomainV2OrderField.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
