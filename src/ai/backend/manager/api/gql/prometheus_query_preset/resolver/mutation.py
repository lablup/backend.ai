"""Prometheus query preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.api_handlers import Sentinel
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
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreatorSpec,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    DeletePresetAction,
    ModifyPresetAction,
)
from ai.backend.manager.types import OptionalState, TriState


@strawberry.mutation(description="Added in 26.3.0. Create a new query definition (admin only).")  # type: ignore[misc]
async def admin_create_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    input: CreateQueryDefinitionInput,
) -> CreateQueryDefinitionPayload:
    check_admin_only()
    processors = info.context.processors
    dto = input.to_pydantic()

    creator: Creator[PrometheusQueryPresetRow] = Creator(
        spec=PrometheusQueryPresetCreatorSpec(
            name=dto.name,
            metric_name=dto.metric_name,
            query_template=dto.query_template,
            time_window=dto.time_window,
            filter_labels=dto.options.filter_labels,
            group_labels=dto.options.group_labels,
        )
    )
    action_result = await processors.prometheus_query_preset.create_preset.wait_for_complete(
        CreatePresetAction(creator=creator)
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
    dto = input.to_pydantic()

    preset_id = UUID(id)
    spec = PrometheusQueryPresetUpdaterSpec(
        name=OptionalState.nop() if dto.name is None else OptionalState.update(dto.name),
        metric_name=OptionalState.nop()
        if dto.metric_name is None
        else OptionalState.update(dto.metric_name),
        query_template=OptionalState.nop()
        if dto.query_template is None
        else OptionalState.update(dto.query_template),
        time_window=TriState.nop()
        if isinstance(dto.time_window, Sentinel)
        else TriState.nullify()
        if dto.time_window is None
        else TriState.update(dto.time_window),
    )
    if dto.options is not None:
        spec.filter_labels = OptionalState.update(dto.options.filter_labels or [])
        spec.group_labels = OptionalState.update(dto.options.group_labels or [])

    action_result = await processors.prometheus_query_preset.modify_preset.wait_for_complete(
        ModifyPresetAction(preset_id=preset_id, updater=Updater(pk_value=preset_id, spec=spec))
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
