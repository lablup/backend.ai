"""Permission fetcher functions."""

from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    PermissionConnection,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
)
from ai.backend.manager.api.gql.rbac.types.permission import PermissionEdge
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.permission_controller.options import (
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)
from ai.backend.manager.services.permission_contoller.actions.search_permissions import (
    SearchPermissionsAction,
)


@lru_cache(maxsize=1)
def get_permission_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScopedPermissionOrders.id(ascending=False),
        backward_order=ScopedPermissionOrders.id(ascending=True),
        forward_condition_factory=ScopedPermissionConditions.by_cursor_forward,
        backward_condition_factory=ScopedPermissionConditions.by_cursor_backward,
        tiebreaker_order=PermissionRow.id.asc(),
    )


async def fetch_permissions(
    info: Info[StrawberryGQLContext],
    filter: PermissionFilter | None = None,
    order_by: list[PermissionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> PermissionConnection:
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_permission_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = (
        await info.context.processors.permission_controller.search_permissions.wait_for_complete(
            SearchPermissionsAction(querier=querier)
        )
    )

    result = action_result.result
    edges = [
        PermissionEdge(
            node=PermissionGQL.from_dataclass(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return PermissionConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
