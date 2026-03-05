"""Prometheus query preset GQL mutation resolvers."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    CreatePrometheusQueryPresetInput,
    CreatePrometheusQueryPresetPayload,
    DeletePrometheusQueryPresetPayload,
    ModifyPrometheusQueryPresetInput,
    ModifyPrometheusQueryPresetPayload,
    PrometheusQueryPresetGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    DeletePresetAction,
    ModifyPresetAction,
)


@strawberry.mutation(description="Create a new prometheus query preset (admin only).")  # type: ignore[misc]
async def admin_create_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    input: CreatePrometheusQueryPresetInput,
) -> CreatePrometheusQueryPresetPayload:
    check_admin_only()
    processors = info.context.processors

    action_result = await processors.prometheus_query_preset.create_preset.wait_for_complete(
        CreatePresetAction(creator=input.to_creator())
    )

    return CreatePrometheusQueryPresetPayload(
        preset=PrometheusQueryPresetGQL.from_data(action_result.preset)
    )


@strawberry.mutation(description="Modify an existing prometheus query preset (admin only).")  # type: ignore[misc]
async def admin_modify_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: ModifyPrometheusQueryPresetInput,
) -> ModifyPrometheusQueryPresetPayload:
    check_admin_only()
    processors = info.context.processors

    preset_id = uuid.UUID(id)
    action_result = await processors.prometheus_query_preset.modify_preset.wait_for_complete(
        ModifyPresetAction(preset_id=preset_id, updater=input.to_updater(preset_id))
    )

    return ModifyPrometheusQueryPresetPayload(
        preset=PrometheusQueryPresetGQL.from_data(action_result.preset)
    )


@strawberry.mutation(description="Delete a prometheus query preset (admin only).")  # type: ignore[misc]
async def admin_delete_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeletePrometheusQueryPresetPayload:
    check_admin_only()
    processors = info.context.processors

    await processors.prometheus_query_preset.delete_preset.wait_for_complete(
        DeletePresetAction(preset_id=uuid.UUID(id))
    )

    return DeletePrometheusQueryPresetPayload(id=id)
