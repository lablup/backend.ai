"""GraphQL resolvers for deployment revision presets."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetFilter,
    DeploymentRevisionPresetOrder,
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    CreateDeploymentRevisionPresetInputGQL,
    CreateDeploymentRevisionPresetPayloadGQL,
    DeleteDeploymentRevisionPresetPayloadGQL,
    DeploymentRevisionPresetConnection,
    DeploymentRevisionPresetEdge,
    DeploymentRevisionPresetFilterGQL,
    DeploymentRevisionPresetGQL,
    DeploymentRevisionPresetOrderByGQL,
    UpdateDeploymentRevisionPresetInputGQL,
    UpdateDeploymentRevisionPresetPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search deployment revision presets.",
    )
)  # type: ignore[misc]
async def deployment_revision_presets(
    info: Info[StrawberryGQLContext],
    filter: DeploymentRevisionPresetFilterGQL | None = None,
    order_by: list[DeploymentRevisionPresetOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DeploymentRevisionPresetConnection | None:
    filter_dto: DeploymentRevisionPresetFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[DeploymentRevisionPresetOrder] | None = None
    if order_by:
        orders_dto = [
            DeploymentRevisionPresetOrder(
                field=DeploymentRevisionPresetOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]
    search_input = SearchDeploymentRevisionPresetsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.deployment_revision_preset.search(search_input)
    edges = [
        DeploymentRevisionPresetEdge(
            node=DeploymentRevisionPresetGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return DeploymentRevisionPresetConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single deployment revision preset by ID.",
    )
)  # type: ignore[misc]
async def deployment_revision_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeploymentRevisionPresetGQL | None:
    node = await info.context.adapters.deployment_revision_preset.get(id)
    return DeploymentRevisionPresetGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a deployment revision preset.",
    )
)  # type: ignore[misc]
async def create_deployment_revision_preset(
    info: Info[StrawberryGQLContext],
    input: CreateDeploymentRevisionPresetInputGQL,
) -> CreateDeploymentRevisionPresetPayloadGQL:
    dto = input.to_pydantic()
    payload = await info.context.adapters.deployment_revision_preset.create(dto)
    return CreateDeploymentRevisionPresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a deployment revision preset.",
    )
)  # type: ignore[misc]
async def update_deployment_revision_preset(
    info: Info[StrawberryGQLContext],
    input: UpdateDeploymentRevisionPresetInputGQL,
) -> UpdateDeploymentRevisionPresetPayloadGQL:
    dto = input.to_pydantic()
    payload = await info.context.adapters.deployment_revision_preset.update(dto)
    return UpdateDeploymentRevisionPresetPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a deployment revision preset.",
    )
)  # type: ignore[misc]
async def delete_deployment_revision_preset(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteDeploymentRevisionPresetPayloadGQL:
    payload = await info.context.adapters.deployment_revision_preset.delete(id)
    return DeleteDeploymentRevisionPresetPayloadGQL.from_pydantic(payload)
