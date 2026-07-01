"""Prometheus query preset category GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    DeleteCategoryInput as DeleteCategoryInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CreateCategoryGQLPayload as CreateCategoryGQLPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.category import (
    CreateCategoryInputGQL,
    CreateCategoryPayloadGQL,
    DeleteCategoryPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Create a new query preset category (admin only).",
    )
)
async def admin_create_prometheus_query_preset_category(
    info: Info[StrawberryGQLContext],
    input: CreateCategoryInputGQL,
) -> CreateCategoryPayloadGQL | None:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset_category.create(
        input.to_pydantic()
    )
    return CreateCategoryPayloadGQL.from_pydantic(CreateCategoryGQLPayloadDTO(category=result.item))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Delete a query preset category (admin only).",
    )
)
async def admin_delete_prometheus_query_preset_category(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteCategoryPayloadGQL | None:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset_category.delete(
        DeleteCategoryInputDTO(id=UUID(id))
    )
    return DeleteCategoryPayloadGQL.from_pydantic(result)
