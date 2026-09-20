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
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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

    id: UUIDFilter | None = None
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
    description: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Filter by project description."
        ),
        default=None,
    )
    integration_name: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by the external integration name.",
        ),
        default=None,
    )
    type: ProjectTypeEnumFilter | None = None
    is_active: bool | None = None
    created_at: DateTimeFilter | None = None
    modified_at: DateTimeFilter | None = None
    domain: ProjectDomainNestedFilter | None = gql_field(
        default=None,
        description="Filter by the domain holding the project.",
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. A filter on another entity's columns"
            " cannot check whether the caller may read that row. Search domains first, then"
            " narrow by `domainName`."
        ),
    )
    user: ProjectUserNestedFilter | None = gql_field(
        default=None,
        description="Filter by the users enrolled in the project.",
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. A filter on another entity's columns"
            " cannot check whether the caller may read that row. Search users first, then pass"
            " their ids as the `user` scope."
        ),
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


_USER_ORDER_DEPRECATION_TEMPLATE = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. A project holds many users, so this order"
    " folds them into a single {subject}. Narrow the results with the `user` filter instead."
)


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
            "DOMAIN_NAME: Order by domain name. "
            "ID: Order by project ID. "
            "DESCRIPTION: Order by project description. "
            "INTEGRATION_NAME: Order by the external integration name. "
            "USER_USERNAME: Order by username. "
            "USER_EMAIL: Order by user email."
        ),
    ),
    name="ProjectV2OrderField",
    deprecated_values={
        "USER_USERNAME": _USER_ORDER_DEPRECATION_TEMPLATE.format(subject="username"),
        "USER_EMAIL": _USER_ORDER_DEPRECATION_TEMPLATE.format(subject="email address"),
    },
)
class ProjectV2OrderField(StrEnum):
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    NAME = "name"
    IS_ACTIVE = "is_active"
    TYPE = "type"
    DOMAIN_NAME = "domain_name"
    ID = "id"
    DESCRIPTION = "description"
    INTEGRATION_NAME = "integration_name"
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
