"""Project V2 GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.group.request import ProjectFilter, ProjectOrder
from ai.backend.common.dto.manager.v2.group.types import (
    ProjectDomainFilter,
    ProjectTypeFilter,
    ProjectUserFilter,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .enums import ProjectTypeEnum


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for the domain a project belongs to. Filters projects whose domain matches all specified conditions.",
        added_version="26.2.0",
    ),
    name="ProjectDomainNestedFilter",
)
class ProjectDomainNestedFilter(PydanticInputMixin[ProjectDomainFilter]):
    """Nested filter for domain of a project."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for users belonging to a project. Filters projects that have at least one user matching all specified conditions.",
        added_version="26.2.0",
    ),
    name="ProjectUserNestedFilter",
)
class ProjectUserNestedFilter(PydanticInputMixin[ProjectUserFilter]):
    """Nested filter for users within a project."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for ProjectTypeEnum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="ProjectTypeV2EnumFilter",
)
class ProjectTypeEnumFilter(PydanticInputMixin[ProjectTypeFilter]):
    """Filter for project type enum fields."""

    equals: ProjectTypeEnum | None = None
    in_: list[ProjectTypeEnum] | None = None
    not_equals: ProjectTypeEnum | None = None
    not_in: list[ProjectTypeEnum] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying projects. Supports filtering by ID, name, domain, type, active status, and timestamps. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.2.0",
    ),
    name="ProjectV2Filter",
)
class ProjectV2Filter(PydanticInputMixin[ProjectFilter]):
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
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Fields available for ordering project query results. "
            "CREATED_AT: Order by creation timestamp. "
            "MODIFIED_AT: Order by last modification timestamp. "
            "NAME: Order by project name alphabetically. "
            "IS_ACTIVE: Order by active status. "
            "TYPE: Order by project type. "
            "DOMAIN_NAME: Order by domain name (scalar subquery). "
            "USER_USERNAME: Order by username (MIN aggregation). "
            "USER_EMAIL: Order by user email (MIN aggregation)."
        ),
    ),
    name="ProjectV2OrderField",
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
    name="ProjectV2OrderBy",
)
class ProjectV2OrderBy(PydanticInputMixin[ProjectOrder]):
    """OrderBy for project queries."""

    field: ProjectV2OrderField = ProjectV2OrderField.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
