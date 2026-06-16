"""AppConfig (merged view) GQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.app_config.request import (
    ScopedSearchAppConfigsInput,
    SearchAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config.types import (
    AppConfigConnectionGQL,
    AppConfigEdgeGQL,
    AppConfigFilterGQL,
    AppConfigGQL,
    AppConfigOrderByGQL,
    AppConfigScopeGQL,
)
from ai.backend.manager.api.gql.app_config_fragment.types import (
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
from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType


def _app_config_id(user_id: object, name: str) -> str:
    """Composite Relay id for the merged view (keyed by `(user_id, name)`)."""
    return f"{user_id}:{name}"


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scoped merged-view AppConfig search (auth required, RBAC-gated). "
            "`scope.userIds` are OR'd; non-admin callers are restricted to "
            "their own user. Self-service is just a USER-scoped search."
        ),
    )
)  # type: ignore[misc]
async def scoped_app_configs(
    info: Info[StrawberryGQLContext],
    scope: AppConfigScopeGQL,
    filter: AppConfigFilterGQL | None = None,
    order_by: list[AppConfigOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigConnectionGQL:
    payload = await info.context.adapters.app_config.scoped_search_app_configs(
        ScopedSearchAppConfigsInput(
            scope=scope.to_pydantic(),
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
    nodes = [
        AppConfigGQL.from_pydantic(item, extra={"id": _app_config_id(item.user_id, item.name)})
        for item in payload.items
    ]
    edges = [AppConfigEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return AppConfigConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Cross-user merged-view search (admin only). Resolves any user's "
            "AppConfig for audit / support. Pin to a single user with "
            "`filter.userId`; otherwise paginates across all users."
        ),
    )
)  # type: ignore[misc]
async def admin_app_configs(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFilterGQL | None = None,
    order_by: list[AppConfigOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AppConfigConnectionGQL:
    check_admin_only()
    payload = await info.context.adapters.app_config.admin_search_app_configs(
        SearchAppConfigsInput(
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
    nodes = [
        AppConfigGQL.from_pydantic(item, extra={"id": _app_config_id(item.user_id, item.name)})
        for item in payload.items
    ]
    edges = [AppConfigEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return AppConfigConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Public (no-auth) `PUBLIC`-scope app-config fragments — the subset of "
            "raw fragments that carry no personally-scoped data."
        ),
    )
)  # type: ignore[misc]
async def public_app_config_fragments(
    info: Info[StrawberryGQLContext],
    filter: AppConfigFragmentFilterGQL | None = None,
    order_by: list[AppConfigFragmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[AppConfigFragmentGQL]:
    payload = await info.context.adapters.app_config_fragment.search(
        scope_type=AppConfigScopeType.PUBLIC,
        scope_id=AppConfigScopeType.PUBLIC.value,
        input=SearchAppConfigFragmentsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    return [AppConfigFragmentGQL.from_pydantic(node) for node in payload.items]
