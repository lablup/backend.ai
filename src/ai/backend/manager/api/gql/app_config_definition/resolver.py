"""GraphQL query and mutation resolvers for app config definitions."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    AppConfigDefinitionConnection,
    AppConfigDefinitionEdge,
    AppConfigDefinitionFilterGQL,
    AppConfigDefinitionGQL,
    AppConfigDefinitionOrderByGQL,
    CreateAppConfigDefinitionInputGQL,
    CreateAppConfigDefinitionPayloadGQL,
    PurgeAppConfigDefinitionInputGQL,
    PurgeAppConfigDefinitionPayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single app config definition by id (super admin only).",
    )
)  # type: ignore[misc]
async def app_config_definition(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> AppConfigDefinitionGQL | None:
    check_admin_only()
    node = await info.context.adapters.app_config_definition.admin_get(id)
    return AppConfigDefinitionGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Search app config definitions with filtering, ordering, and pagination "
            "(super admin only)."
        ),
    )
)  # type: ignore[misc]
async def app_config_definitions(
    info: Info[StrawberryGQLContext],
    filter: AppConfigDefinitionFilterGQL | None = None,
    order_by: list[AppConfigDefinitionOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigDefinitionConnection | None:
    check_admin_only()
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.app_config_definition.admin_search(
        SearchAppConfigDefinitionsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [AppConfigDefinitionGQL.from_pydantic(node) for node in payload.items]
    edges = [
        AppConfigDefinitionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return AppConfigDefinitionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Register a new app config definition (super admin only).",
    )
)
async def admin_create_app_config_definition(
    info: Info[StrawberryGQLContext],
    input: CreateAppConfigDefinitionInputGQL,
) -> CreateAppConfigDefinitionPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.app_config_definition.admin_create(input.to_pydantic())
    return CreateAppConfigDefinitionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge an app config definition by id (super admin only).",
    )
)
async def admin_purge_app_config_definition(
    info: Info[StrawberryGQLContext],
    input: PurgeAppConfigDefinitionInputGQL,
) -> PurgeAppConfigDefinitionPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.app_config_definition.admin_purge(input.to_pydantic())
    return PurgeAppConfigDefinitionPayloadGQL.from_pydantic(payload)
