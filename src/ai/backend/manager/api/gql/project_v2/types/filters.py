"""Project V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.common.dto.manager.v2.group.request import GroupFilter, GroupOrder
from ai.backend.common.dto.manager.v2.group.types import (
    GroupDomainFilter,
    GroupOrderField,
    GroupUserFilter,
    ProjectTypeFilter,
)
from ai.backend.common.dto.manager.v2.group.types import (
    OrderDirection as OrderDirectionDTO,
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

from .enums import ProjectTypeEnum


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for the domain a project belongs to. Filters projects whose domain matches all specified conditions.",
        added_version="26.2.0",
    ),
    model=GroupDomainFilter,
    name="ProjectDomainNestedFilter",
)
class ProjectDomainNestedFilter:
    """Nested filter for domain of a project."""

    name: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> GroupDomainFilter:
        return GroupDomainFilter(
            name=self.name.to_pydantic() if self.name else None,
            is_active=self.is_active,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for users belonging to a project. Filters projects that have at least one user matching all specified conditions.",
        added_version="26.2.0",
    ),
    model=GroupUserFilter,
    name="ProjectUserNestedFilter",
)
class ProjectUserNestedFilter:
    """Nested filter for users within a project."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None

    def to_pydantic(self) -> GroupUserFilter:
        return GroupUserFilter(
            username=self.username.to_pydantic() if self.username else None,
            email=self.email.to_pydantic() if self.email else None,
            is_active=self.is_active,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for ProjectTypeEnum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    model=ProjectTypeFilter,
    name="ProjectTypeV2EnumFilter",
)
class ProjectTypeEnumFilter:
    """Filter for project type enum fields."""

    equals: ProjectTypeEnum | None = None
    in_: list[ProjectTypeEnum] | None = None
    not_equals: ProjectTypeEnum | None = None
    not_in: list[ProjectTypeEnum] | None = None

    def to_pydantic(self) -> ProjectTypeFilter:
        from ai.backend.common.dto.manager.v2.group.types import ProjectType

        return ProjectTypeFilter(
            equals=ProjectType(self.equals.value) if self.equals else None,
            in_=[ProjectType(t.value) for t in self.in_] if self.in_ else None,
            not_equals=ProjectType(self.not_equals.value) if self.not_equals else None,
            not_in=[ProjectType(t.value) for t in self.not_in] if self.not_in else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying projects. Supports filtering by ID, name, domain, type, active status, and timestamps. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.2.0",
    ),
    model=GroupFilter,
    name="ProjectV2Filter",
)
class ProjectV2Filter:
    """Filter for project queries."""

    id: UUIDFilter | None = None
    name: StringFilter | None = None
    domain_name: StringFilter | None = None
    type: ProjectTypeEnumFilter | None = None
    is_active: bool | None = None
    created_at: DateTimeFilter | None = None
    modified_at: DateTimeFilter | None = None
    domain: ProjectDomainNestedFilter | None = None
    user: ProjectUserNestedFilter | None = None
    AND: list[ProjectV2Filter] | None = None
    OR: list[ProjectV2Filter] | None = None
    NOT: list[ProjectV2Filter] | None = None

    def to_pydantic(self) -> GroupFilter:
        return GroupFilter(
            id=self.id.to_pydantic() if self.id else None,
            name=self.name.to_pydantic() if self.name else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            type=self.type.to_pydantic() if self.type else None,
            is_active=self.is_active,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            modified_at=self.modified_at.to_pydantic() if self.modified_at else None,
            domain=self.domain.to_pydantic() if self.domain else None,
            user=self.user.to_pydantic() if self.user else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for project query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.2.0",
    ),
    model=GroupOrder,
    name="ProjectV2OrderBy",
)
class ProjectV2OrderBy:
    """OrderBy for project queries."""

    field: ProjectV2OrderField = ProjectV2OrderField.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> GroupOrder:
        direction = (
            OrderDirectionDTO.ASC
            if self.direction == OrderDirection.ASC
            else OrderDirectionDTO.DESC
        )
        match self.field:
            case ProjectV2OrderField.CREATED_AT:
                return GroupOrder(field=GroupOrderField.CREATED_AT, direction=direction)
            case ProjectV2OrderField.MODIFIED_AT:
                return GroupOrder(field=GroupOrderField.MODIFIED_AT, direction=direction)
            case ProjectV2OrderField.NAME:
                return GroupOrder(field=GroupOrderField.NAME, direction=direction)
            case ProjectV2OrderField.IS_ACTIVE:
                return GroupOrder(field=GroupOrderField.IS_ACTIVE, direction=direction)
            case ProjectV2OrderField.TYPE:
                return GroupOrder(field=GroupOrderField.TYPE, direction=direction)
            case ProjectV2OrderField.DOMAIN_NAME:
                return GroupOrder(field=GroupOrderField.DOMAIN_NAME, direction=direction)
            case ProjectV2OrderField.USER_USERNAME:
                return GroupOrder(field=GroupOrderField.USER_USERNAME, direction=direction)
            case ProjectV2OrderField.USER_EMAIL:
                return GroupOrder(field=GroupOrderField.USER_EMAIL, direction=direction)
