"""Prometheus query preset GQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    CreateQueryDefinitionGQLPayload as CreateQueryDefinitionGQLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    ModifyQueryDefinitionGQLPayload as ModifyQueryDefinitionGQLPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import parse_uuid, to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.inputs import (
    CreateQueryDefinitionInput,
    ModifyQueryDefinitionInput,
    PartialBulkPurgeQueryDefinitionsInputGQL,
    PartialBulkUpdateQueryDefinitionsInputGQL,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.node import (
    CreateQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
    PartialBulkQueryDefinitionsPayloadGQL,
    QueryDefinitionGQL,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.payloads import (
    DeleteQueryDefinitionPayload,
    PurgeQueryDefinitionPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Create a new query definition (admin only)"
    )
)
async def admin_create_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    input: CreateQueryDefinitionInput,
) -> CreateQueryDefinitionPayload | None:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.create(input.to_pydantic())
    return CreateQueryDefinitionPayload.from_pydantic(
        CreateQueryDefinitionGQLPayloadDTO(preset=result.item)
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a query definition. Only provided fields will be updated.",
    )
)
async def update_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: ModifyQueryDefinitionInput,
) -> ModifyQueryDefinitionPayload:
    result = await info.context.adapters.prometheus_query_preset.update(id, input.to_pydantic())
    return ModifyQueryDefinitionPayload.from_pydantic(
        ModifyQueryDefinitionGQLPayloadDTO(preset=result.item)
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Permanently remove a query definition."
    )
)
async def purge_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeQueryDefinitionPayload:
    result = await info.context.adapters.prometheus_query_preset.purge(PrometheusQueryPresetID(id))
    return PurgeQueryDefinitionPayload.from_pydantic(
        result, extra={"purged_id": to_global_id(QueryDefinitionGQL, result.entity_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several query definitions, answering for each one.",
    )
)
async def partial_bulk_update_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateQueryDefinitionsInputGQL,
) -> PartialBulkQueryDefinitionsPayloadGQL:
    payload = await info.context.adapters.prometheus_query_preset.partial_bulk_update(
        input.to_pydantic()
    )
    return PartialBulkQueryDefinitionsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several query definitions, answering for each one.",
    )
)
async def partial_bulk_purge_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeQueryDefinitionsInputGQL,
) -> PartialBulkQueryDefinitionsPayloadGQL:
    payload = await info.context.adapters.prometheus_query_preset.partial_bulk_purge(
        input.to_pydantic()
    )
    return PartialBulkQueryDefinitionsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Modify an existing query definition (admin only)."
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updatePrometheusQueryPreset`."
    ),
)
async def admin_modify_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
    input: ModifyQueryDefinitionInput,
) -> ModifyQueryDefinitionPayload | None:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.update(
        parse_uuid(id), input.to_pydantic()
    )
    return ModifyQueryDefinitionPayload.from_pydantic(
        ModifyQueryDefinitionGQLPayloadDTO(preset=result.item)
    )


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Delete a query definition (admin only)"),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgePrometheusQueryPreset`.",
)
async def admin_delete_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> DeleteQueryDefinitionPayload | None:
    check_admin_only()
    result = await info.context.adapters.prometheus_query_preset.purge(
        PrometheusQueryPresetID(parse_uuid(id))
    )
    return DeleteQueryDefinitionPayload.from_pydantic(result)
