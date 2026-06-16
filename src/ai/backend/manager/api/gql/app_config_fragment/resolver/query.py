"""AppConfigFragment GQL query resolvers.

Per the scope-bound list is exposed via child fields on
`DomainV2.appConfigFragments` / `UserV2.appConfigFragments`, not as a
root resolver. Only the single-row read and the cross-scope admin
search live here. The scope-bound REST endpoint
`POST /v2/app-config-fragments/{scope_type}/{scope_id}/search`
continues to use the adapter's `search()` method directly.
"""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentKeyInput,
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types import (
    AppConfigFragmentConnectionGQL,
    AppConfigFragmentEdgeGQL,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Get a single app-config fragment by natural key "
            "`(scope_type, scope_id, name)`. Available to any authenticated user "
            "— service-layer authorization gates cross-scope reads."
        ),
    )
)  # type: ignore[misc]
async def app_config_fragment(
    info: Info[StrawberryGQLContext],
    scope_type: AppConfigScopeType,
    scope_id: str,
    name: str,
) -> AppConfigFragmentGQL | None:
    payload = await info.context.adapters.app_config_fragment.get(
        AppConfigFragmentKeyInput(scope_type=scope_type, scope_id=scope_id, name=name)
    )
    if payload.item is None:
        return None
    return AppConfigFragmentGQL.from_pydantic(payload.item)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cross-scope admin search across all app-config fragments (admin only).",
    )
)  # type: ignore[misc]
async def admin_app_config_fragments(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFragmentFilterGQL | None = None,
    order_by: list[AppConfigFragmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigFragmentConnectionGQL:
    check_admin_only()
    payload = await info.context.adapters.app_config_fragment.admin_search(
        SearchAppConfigFragmentsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [AppConfigFragmentGQL.from_pydantic(node) for node in payload.items]
    edges = [AppConfigFragmentEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return AppConfigFragmentConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
