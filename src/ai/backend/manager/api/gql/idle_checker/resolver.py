from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.idle_checker.request import SearchIdleCheckersInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.idle_checker.types import (
    CreateIdleCheckerInputGQL,
    CreateIdleCheckerPayloadGQL,
    IdleCheckerConnectionGQL,
    IdleCheckerEdgeGQL,
    IdleCheckerFilterGQL,
    IdleCheckerGQL,
    IdleCheckerOrderByGQL,
    PurgeIdleCheckerInputGQL,
    PurgeIdleCheckerPayloadGQL,
    UpdateIdleCheckerInputGQL,
    UpdateIdleCheckerPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches global idle checker definitions with filtering, ordering, and "
            "pagination (super admin only)."
        ),
    )
)
async def admin_idle_checkers(
    info: Info[StrawberryGQLContext],
    filter: IdleCheckerFilterGQL | None = None,
    order_by: list[IdleCheckerOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerConnectionGQL:
    check_admin_only()
    payload = await info.context.adapters.idle_checker.admin_search(
        SearchIdleCheckersInput(
            filter=filter.to_pydantic() if filter else None,
            order=[order.to_pydantic() for order in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [IdleCheckerGQL.from_pydantic(item) for item in payload.items]
    edges = [IdleCheckerEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return IdleCheckerConnectionGQL(
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
        description="Creates a global idle checker definition (super admin only).",
    )
)
async def admin_create_idle_checker(
    info: Info[StrawberryGQLContext],
    input: CreateIdleCheckerInputGQL,
) -> CreateIdleCheckerPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.idle_checker.admin_create(input.to_pydantic())
    return CreateIdleCheckerPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Updates a global idle checker definition (super admin only).",
    )
)
async def admin_update_idle_checker(
    info: Info[StrawberryGQLContext],
    input: UpdateIdleCheckerInputGQL,
) -> UpdateIdleCheckerPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.idle_checker.admin_update(input.to_pydantic())
    return UpdateIdleCheckerPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently removes a global idle checker (super admin only).",
    )
)
async def admin_purge_idle_checker(
    info: Info[StrawberryGQLContext],
    input: PurgeIdleCheckerInputGQL,
) -> PurgeIdleCheckerPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.idle_checker.admin_purge(input.to_pydantic())
    return PurgeIdleCheckerPayloadGQL.from_pydantic(payload)
