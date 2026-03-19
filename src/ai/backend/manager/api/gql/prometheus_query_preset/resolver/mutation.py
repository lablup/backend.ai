"""Prometheus query preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    DeleteQueryDefinitionInput as DeleteQueryDefinitionInputDTO,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.mutation(description="Added in 26.3.0. Create a new query definition (admin only).")  # type: ignore[misc]
async def admin_create_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    input: CreateQueryDefinitionInput,
) -> CreateQueryDefinitionPayload:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.create(input.to_pydantic())
    return CreateQueryDefinitionPayload.from_pydantic(result)


@strawberry.mutation(
    description="Added in 26.3.0. Modify an existing query definition (admin only)."
)  # type: ignore[misc]
async def admin_modify_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: ModifyQueryDefinitionInput,
) -> ModifyQueryDefinitionPayload:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.update(
        UUID(id), input.to_pydantic()
    )
    return ModifyQueryDefinitionPayload.from_pydantic(result)


@strawberry.mutation(description="Added in 26.3.0. Delete a query definition (admin only).")  # type: ignore[misc]
async def admin_delete_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteQueryDefinitionPayload:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.delete(
        DeleteQueryDefinitionInputDTO(id=UUID(id))
    )
    return DeleteQueryDefinitionPayload.from_pydantic(result)
