"""Prometheus query preset category GQL types (output, filter, input, payload)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryFilter as CategoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryOrder as CategoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CreateCategoryInput as CreateCategoryInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CreateCategoryGQLPayload as CreateCategoryGQLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    DeleteCategoryPayload as DeleteCategoryPayloadDTO,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

# --- Output type ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Prometheus query preset category.",
    ),
    model=CategoryNode,
    name="QueryPresetCategory",
)
class CategoryGQL(PydanticOutputMixin[CategoryNode]):
    id: UUID = gql_field(description="Category UUID.")
    name: str = gql_field(description="Human-readable category name.")
    description: str | None = gql_field(description="Optional category description.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")


# --- Filter / Order types ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying query preset categories.",
        added_version="26.3.0",
    ),
    name="CategoryFilter",
)
class CategoryFilterGQL(PydanticInputMixin[CategoryFilterDTO]):
    name: StringFilter | None = gql_field(description="Filter by name.", default=None)
    AND: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Match all of the given sub-filters."),
        default=None,
    )
    OR: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Match any of the given sub-filters."),
        default=None,
    )
    NOT: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(added_version="26.7.0", description="Negate the given sub-filters."),
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering query preset category results.",
    ),
    name="CategoryOrderField",
)
class CategoryOrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for query preset category results.",
        added_version="26.3.0",
    ),
    name="CategoryOrderBy",
)
class CategoryOrderByGQL(PydanticInputMixin[CategoryOrderDTO]):
    field: CategoryOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.", default=OrderDirection.DESC
    )


# --- Input types ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new query preset category.",
        added_version="26.3.0",
    ),
    name="CreateCategoryInput",
)
class CreateCategoryInputGQL(PydanticInputMixin[CreateCategoryInputDTO]):
    name: str = gql_field(description="Human-readable category name (must be unique).")
    description: str | None = gql_field(description="Optional category description.", default=None)


# --- Payload types ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after creating a query preset category.",
    ),
    model=CreateCategoryGQLPayloadDTO,
    name="CreateCategoryPayload",
)
class CreateCategoryPayloadGQL(PydanticOutputMixin[CreateCategoryGQLPayloadDTO]):
    category: CategoryGQL = gql_field(description="Created category.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after deleting a query preset category.",
    ),
    model=DeleteCategoryPayloadDTO,
    name="DeleteCategoryPayload",
)
class DeleteCategoryPayloadGQL(PydanticOutputMixin[DeleteCategoryPayloadDTO]):
    id: UUID = gql_field(description="Deleted category ID.")
