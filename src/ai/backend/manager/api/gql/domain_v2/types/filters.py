"""Domain V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

import strawberry

from ai.backend.common.dto.manager.v2.domain.request import DomainFilter, DomainOrder
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    DomainProjectFilter,
    DomainUserFilter,
)
from ai.backend.common.dto.manager.v2.domain.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for projects belonging to a domain. Filters domains that have at least one project matching all specified conditions.",
        added_version="26.2.0",
    ),
    model=DomainProjectFilter,
    name="DomainProjectNestedFilter",
)
class DomainProjectNestedFilter:
    """Nested filter for projects within a domain."""

    name: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> DomainProjectFilter:
        return DomainProjectFilter(
            name=self.name.to_pydantic() if self.name else None,
            is_active=self.is_active,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for users belonging to a domain. Filters domains that have at least one user matching all specified conditions.",
        added_version="26.2.0",
    ),
    model=DomainUserFilter,
    name="DomainUserNestedFilter",
)
class DomainUserNestedFilter:
    """Nested filter for users within a domain."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> DomainUserFilter:
        return DomainUserFilter(
            username=self.username.to_pydantic() if self.username else None,
            email=self.email.to_pydantic() if self.email else None,
            is_active=self.is_active,
        )


@strawberry.input(
    name="DomainV2Filter",
    description="Added in 26.2.0. Filter input for querying domains. Supports filtering by name, description, active status, timestamps, and nested project/user filters. Multiple filters can be combined using AND, OR, and NOT logical operators.",
)
class DomainV2Filter:
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

    def to_pydantic(self) -> DomainFilter:
        return DomainFilter(
            name=self.name.to_pydantic() if self.name else None,
            description=self.description.to_pydantic() if self.description else None,
            is_active=self.is_active,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            modified_at=self.modified_at.to_pydantic() if self.modified_at else None,
            project=self.project.to_pydantic() if self.project else None,
            user=self.user.to_pydantic() if self.user else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for domain query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.2.0",
    ),
    model=DomainOrder,
    name="DomainV2OrderBy",
)
class DomainV2OrderBy:
    """OrderBy for domain queries."""

    field: DomainV2OrderField = DomainV2OrderField.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> DomainOrder:
        ascending = self.direction == OrderDirection.ASC
        direction = OrderDirectionDTO.ASC if ascending else OrderDirectionDTO.DESC
        match self.field:
            case DomainV2OrderField.CREATED_AT:
                return DomainOrder(field=DomainOrderField.CREATED_AT, direction=direction)
            case DomainV2OrderField.MODIFIED_AT:
                return DomainOrder(field=DomainOrderField.MODIFIED_AT, direction=direction)
            case DomainV2OrderField.NAME:
                return DomainOrder(field=DomainOrderField.NAME, direction=direction)
            case DomainV2OrderField.IS_ACTIVE:
                return DomainOrder(field=DomainOrderField.IS_ACTIVE, direction=direction)
            case DomainV2OrderField.PROJECT_NAME:
                return DomainOrder(field=DomainOrderField.PROJECT_NAME, direction=direction)
            case DomainV2OrderField.USER_USERNAME:
                return DomainOrder(field=DomainOrderField.USER_USERNAME, direction=direction)
            case DomainV2OrderField.USER_EMAIL:
                return DomainOrder(field=DomainOrderField.USER_EMAIL, direction=direction)
