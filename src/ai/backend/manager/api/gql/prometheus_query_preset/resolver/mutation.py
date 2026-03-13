"""Prometheus query preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionPayload,
    QueryDefinitionGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    DeletePresetAction,
    ModifyPresetAction,
)


@strawberry.mutation(description="Added in 26.3.0. Create a new query definition (admin only).")  # type: ignore[misc]
async def admin_create_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    input: CreateQueryDefinitionInput,
) -> CreateQueryDefinitionPayload:
    check_admin_only()
    processors = info.context.processors

    action_result = await processors.prometheus_query_preset.create_preset.wait_for_complete(
        CreatePresetAction(creator=input.to_creator())
    )

    return CreateQueryDefinitionPayload(preset=QueryDefinitionGQL.from_data(action_result.preset))


@strawberry.mutation(
    description="Added in 26.3.0. Modify an existing query definition (admin only)."
)  # type: ignore[misc]
async def admin_modify_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: ModifyQueryDefinitionInput,
) -> ModifyQueryDefinitionPayload:
    check_admin_only()
    processors = info.context.processors

    preset_id = UUID(id)
    action_result = await processors.prometheus_query_preset.modify_preset.wait_for_complete(
        ModifyPresetAction(preset_id=preset_id, updater=input.to_updater(preset_id))
    )

    return ModifyQueryDefinitionPayload(preset=QueryDefinitionGQL.from_data(action_result.preset))


@strawberry.mutation(description="Added in 26.3.0. Delete a query definition (admin only).")  # type: ignore[misc]
async def admin_delete_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteQueryDefinitionPayload:
    check_admin_only()
    processors = info.context.processors

    await processors.prometheus_query_preset.delete_preset.wait_for_complete(
        DeletePresetAction(preset_id=UUID(id))
    )

    return DeleteQueryDefinitionPayload(id=id)
