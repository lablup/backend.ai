"""GraphQL query and mutation resolvers for app config allow-list entries."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    SearchAppConfigAllowListInput,
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
    AppConfigAllowListConnection,
    AppConfigAllowListEdge,
    AppConfigAllowListFilterGQL,
    AppConfigAllowListGQL,
    AppConfigAllowListOrderByGQL,
    CreateAppConfigAllowListInputGQL,
    CreateAppConfigAllowListPayloadGQL,
    PurgeAppConfigAllowListPayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single app config allow-list entry by id (super admin only).",
    )
)  # type: ignore[misc]
async def admin_app_config_allow_list(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> AppConfigAllowListGQL | None:
    check_admin_only()
    node = await info.context.adapters.app_config_allow_list.admin_get(id)
    return AppConfigAllowListGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Search app config allow-list entries with filtering, ordering, and pagination "
            "(super admin only)."
        ),
    )
)  # type: ignore[misc]
async def admin_app_config_allow_lists(
    info: Info[StrawberryGQLContext],
    filter: AppConfigAllowListFilterGQL | None = None,
    order_by: list[AppConfigAllowListOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigAllowListConnection | None:
    check_admin_only()
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.app_config_allow_list.admin_search(
        SearchAppConfigAllowListInput(
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

    nodes = [AppConfigAllowListGQL.from_pydantic(node) for node in payload.items]
    edges = [
        AppConfigAllowListEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return AppConfigAllowListConnection(
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
        description="Register a new app config allow-list entry (super admin only).",
    )
)
async def admin_create_app_config_allow_list(
    info: Info[StrawberryGQLContext],
    input: CreateAppConfigAllowListInputGQL,
) -> CreateAppConfigAllowListPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.app_config_allow_list.admin_create(input.to_pydantic())
    return CreateAppConfigAllowListPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge an app config allow-list entry by id (super admin only).",
    )
)
async def admin_purge_app_config_allow_list(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeAppConfigAllowListPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.app_config_allow_list.admin_purge(id)
    return PurgeAppConfigAllowListPayloadGQL.from_pydantic(payload)
