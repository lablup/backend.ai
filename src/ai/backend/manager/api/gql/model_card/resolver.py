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
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    ModelCardFilter,
    ModelCardOrder,
    SearchModelCardsInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import SearchModelCardsPayload
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardOrderField
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetConnection,
    DeploymentRevisionPresetEdge,
    DeploymentRevisionPresetFilterGQL,
    DeploymentRevisionPresetGQL,
    DeploymentRevisionPresetOrderByGQL,
)
from ai.backend.manager.api.gql.model_card.types import (
    CreateModelCardInputGQL,
    CreateModelCardPayloadGQL,
    DeleteModelCardPayloadGQL,
    DeleteModelCardsInputGQL,
    DeleteModelCardsPayloadGQL,
    DeployModelCardInputGQL,
    DeployModelCardPayloadGQL,
    ModelCardAvailablePresetsScopeGQL,
    ModelCardFilterGQL,
    ModelCardGQL,
    ModelCardOrderByGQL,
    ModelCardV2Connection,
    ModelCardV2Edge,
    ProjectModelCardScopeGQL,
    ScanProjectModelCardsPayloadGQL,
    UpdateModelCardInputGQL,
    UpdateModelCardPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search all model cards (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_model_cards_v2(
    info: Info[StrawberryGQLContext],
    filter: ModelCardFilterGQL | None = None,
    order_by: list[ModelCardOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelCardV2Connection | None:
    check_admin_only()
    search_input = _build_search_input(filter, order_by, first, after, last, before, limit, offset)
    result = await info.context.adapters.model_card.admin_search(search_input)
    return _build_connection(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search model cards within a MODEL_STORE project.",
    )
)  # type: ignore[misc]
async def project_model_cards_v2(
    info: Info[StrawberryGQLContext],
    scope: ProjectModelCardScopeGQL,
    filter: ModelCardFilterGQL | None = None,
    order_by: list[ModelCardOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelCardV2Connection | None:
    search_input = _build_search_input(filter, order_by, first, after, last, before, limit, offset)
    result = await info.context.adapters.model_card.project_search(scope.project_id, search_input)
    return _build_connection(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single model card by ID.",
    )
)  # type: ignore[misc]
async def model_card_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> ModelCardGQL | None:
    node = await info.context.adapters.model_card.get(id)
    return ModelCardGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_model_card_v2(
    info: Info[StrawberryGQLContext],
    input: CreateModelCardInputGQL,
) -> CreateModelCardPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.model_card.create(dto)
    return CreateModelCardPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_update_model_card_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateModelCardInputGQL,
) -> UpdateModelCardPayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    payload = await info.context.adapters.model_card.update(dto)
    return UpdateModelCardPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a model card (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_model_card_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteModelCardPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.model_card.delete(id)
    return DeleteModelCardPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete multiple model cards (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_model_cards_v2(
    info: Info[StrawberryGQLContext],
    input: DeleteModelCardsInputGQL,
) -> DeleteModelCardsPayloadGQL:
    """Delete multiple model cards.

    Args:
        info: Strawberry GraphQL context.
        input: Input containing list of model card UUIDs to delete.

    Returns:
        DeleteModelCardsPayloadGQL with count of deleted model cards.
    """
    check_admin_only()
    ctx = info.context
    dto = input.to_pydantic()
    payload = await ctx.adapters.model_card.bulk_delete(dto)
    return DeleteModelCardsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scan a MODEL_STORE project and upsert model cards from vfolder model-definition.yaml files.",
    )
)  # type: ignore[misc]
async def scan_project_model_cards_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> ScanProjectModelCardsPayloadGQL:
    payload = await info.context.adapters.model_card.scan_project(project_id)
    return ScanProjectModelCardsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deploy a model card by creating a deployment with a revision preset.",
    )
)  # type: ignore[misc]
async def deploy_model_card_v2(
    info: Info[StrawberryGQLContext],
    card_id: UUID,
    input: DeployModelCardInputGQL,
) -> DeployModelCardPayloadGQL:
    payload = await info.context.adapters.model_card.deploy(card_id, input.to_pydantic())
    return DeployModelCardPayloadGQL.from_pydantic(payload)


def _build_search_input(
    filter: ModelCardFilterGQL | None,
    order_by: list[ModelCardOrderByGQL] | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    limit: int | None,
    offset: int | None,
) -> SearchModelCardsInput:
    filter_dto: ModelCardFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[ModelCardOrder] | None = None
    if order_by:
        orders_dto = [
            ModelCardOrder(
                field=ModelCardOrderField(o.field.value),
                direction=OrderDirection(o.direction),
            )
            for o in order_by
        ]
    return SearchModelCardsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search deployment revision presets that satisfy a model card's minimum resource requirements.",
    )
)  # type: ignore[misc]
async def model_card_available_presets_v2(
    info: Info[StrawberryGQLContext],
    scope: ModelCardAvailablePresetsScopeGQL,
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
    result = await info.context.adapters.model_card.available_presets(
        scope.model_card_id, search_input
    )
    return _build_preset_connection(result)


def _build_preset_connection(
    result: SearchDeploymentRevisionPresetsPayload,
) -> DeploymentRevisionPresetConnection:
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


def _build_connection(result: SearchModelCardsPayload) -> ModelCardV2Connection:
    edges = [
        ModelCardV2Edge(
            node=ModelCardGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return ModelCardV2Connection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
