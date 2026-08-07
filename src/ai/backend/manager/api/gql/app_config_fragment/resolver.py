"""GraphQL query and mutation resolvers for app config fragments.

Only the system-wide search is superadmin-only. Every other field is auth-level: a user
writes and reads their own user-scope fragments, a domain admin their domain's, and the RBAC
validators the processors run decide that — not this layer.
"""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    ScopedAppConfigFragmentsByNamesInput,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    AppConfigFragmentConnection,
    AppConfigFragmentEdge,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigScopeRefGQL,
    MyUpsertAppConfigFragmentsInputGQL,
    ScopedUpsertAppConfigFragmentsInputGQL,
    UpsertAppConfigFragmentsPayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description="Get a single app config fragment by id.",
    )
)  # type: ignore[misc]
async def app_config_fragment(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> AppConfigFragmentGQL | None:
    node = await info.context.adapters.app_config_fragment.get(AppConfigFragmentID(id))
    return AppConfigFragmentGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Search app config fragments across every scope with filtering, ordering, and "
            "pagination (super admin only)."
        ),
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
) -> AppConfigFragmentConnection | None:
    check_admin_only()
    payload = await info.context.adapters.app_config_fragment.admin_search(
        AdminSearchAppConfigFragmentInput(
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
    edges = [AppConfigFragmentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return AppConfigFragmentConnection(
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
        added_version="26.8.0",
        description=(
            "Upsert many app config fragments at one scope (insert, or replace config on "
            "conflict), all-or-nothing. RBAC-authorized at that scope."
        ),
    )
)
async def scoped_upsert_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: ScopedUpsertAppConfigFragmentsInputGQL,
) -> UpsertAppConfigFragmentsPayloadGQL:
    payload = await info.context.adapters.app_config_fragment.scoped_upsert_app_config_fragments(
        input.to_pydantic()
    )
    return UpsertAppConfigFragmentsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Upsert many app config fragments at the current user's own user scope, all-or-nothing."
        ),
    )
)
async def my_upsert_app_config_fragments(
    info: Info[StrawberryGQLContext],
    input: MyUpsertAppConfigFragmentsInputGQL,
) -> UpsertAppConfigFragmentsPayloadGQL:
    payload = await info.context.adapters.app_config_fragment.my_upsert_app_config_fragments(
        input.to_pydantic()
    )
    return UpsertAppConfigFragmentsPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Read the fragments written at one scope for the given config names — the current "
            "values, to inspect before editing them. Answered position by position, null "
            "where the scope holds no fragment for that name. RBAC-authorized at that scope."
        ),
    )
)  # type: ignore[misc]
async def scoped_app_config_fragments_by_names(
    info: Info[StrawberryGQLContext],
    scope: AppConfigScopeRefGQL,
    config_names: list[str],
) -> list[AppConfigFragmentGQL | None]:
    nodes = await info.context.adapters.app_config_fragment.scoped_app_config_fragments_by_names(
        ScopedAppConfigFragmentsByNamesInput(scope=scope.to_pydantic(), config_names=config_names)
    )
    return [
        AppConfigFragmentGQL.from_pydantic(node) if node is not None else None for node in nodes
    ]


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Read the current user's own user-scope fragments for the given config names, "
            "position by position, null where the scope holds no fragment for that name."
        ),
    )
)  # type: ignore[misc]
async def my_app_config_fragments_by_names(
    info: Info[StrawberryGQLContext],
    config_names: list[str],
) -> list[AppConfigFragmentGQL | None]:
    nodes = await info.context.adapters.app_config_fragment.my_app_config_fragments_by_names(
        MyAppConfigFragmentsByNamesInput(config_names=config_names)
    )
    return [
        AppConfigFragmentGQL.from_pydantic(node) if node is not None else None for node in nodes
    ]
