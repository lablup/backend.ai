"""AppConfigPolicy GQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminSearchAppConfigPoliciesInput,
)
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_policy.types import (
    AppConfigPolicyConnectionGQL,
    AppConfigPolicyEdgeGQL,
    AppConfigPolicyFilterGQL,
    AppConfigPolicyGQL,
    AppConfigPolicyOrderByGQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Get a single app-config policy by row id. Available to any authenticated user."
        ),
    )
)  # type: ignore[misc]
async def app_config_policy(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> AppConfigPolicyGQL | None:
    payload = await info.context.adapters.app_config_policy.get(AppConfigPolicyID(id))
    if payload.item is None:
        return None
    return AppConfigPolicyGQL.from_pydantic(payload.item)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List app-config policies with filtering and pagination. Available to any "
            "authenticated user."
        ),
    )
)  # type: ignore[misc]
async def app_config_policies(
    info: Info[StrawberryGQLContext],
    filter: AppConfigPolicyFilterGQL | None = None,
    order_by: list[AppConfigPolicyOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigPolicyConnectionGQL:
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.app_config_policy.admin_search(
        AdminSearchAppConfigPoliciesInput(
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
    nodes = [AppConfigPolicyGQL.from_pydantic(node) for node in payload.items]
    edges = [
        AppConfigPolicyEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]
    return AppConfigPolicyConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
