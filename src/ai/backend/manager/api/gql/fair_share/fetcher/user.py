"""User Fair Share fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.adapters.pagination import (
    PaginationOptions,
    PaginationSpec,
    build_pagination,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.fair_share.types import (
    RGUserFairShareFilter,
    UserFairShareConnection,
    UserFairShareEdge,
    UserFairShareFilter,
    UserFairShareGQL,
    UserFairShareOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.fair_share.conditions import UserFairShareConditions
from ai.backend.manager.models.fair_share.orders import UserFairShareOrders
from ai.backend.manager.models.fair_share.row import UserFairShareRow
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
from ai.backend.manager.repositories.fair_share.types import UserFairShareSearchScope
from ai.backend.manager.services.fair_share.actions import (
    GetUserFairShareAction,
    SearchRGUserFairSharesAction,
    SearchUserFairSharesAction,
)


@lru_cache(maxsize=1)
def get_user_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=UserFairShareOrders.by_created_at(ascending=False),
        backward_order=UserFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=UserFairShareConditions.by_cursor_forward,
        backward_condition_factory=UserFairShareConditions.by_cursor_backward,
        tiebreaker_order=UserFairShareRow.id.asc(),
    )


def _build_user_querier(
    spec: PaginationSpec,
    filter: UserFairShareFilter | RGUserFairShareFilter | None,
    order_by: list[UserFairShareOrderBy] | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    limit: int | None,
    offset: int | None,
    base_conditions: list[QueryCondition] | None,
) -> BatchQuerier:
    is_cursor = first is not None or last is not None
    all_conditions: list[QueryCondition] = list(base_conditions or [])
    if filter is not None:
        all_conditions.extend(filter.build_conditions())
    all_orders: list[QueryOrder] = [o.to_query_order() for o in order_by] if order_by else []
    if not all_orders and not is_cursor:
        all_orders.append(spec.forward_order)
    all_orders.append(spec.tiebreaker_order)
    pagination = build_pagination(
        PaginationOptions(
            first=first, after=after, last=last, before=before, limit=limit, offset=offset
        ),
        spec,
    )
    return BatchQuerier(conditions=all_conditions, orders=all_orders, pagination=pagination)


async def fetch_user_fair_shares(
    info: Info[StrawberryGQLContext],
    filter: UserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> UserFairShareConnection:
    """Fetch user fair shares with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., project_id filter)
    """
    processors = info.context.processors
    querier = _build_user_querier(
        get_user_fair_share_pagination_spec(),
        filter,
        order_by,
        first,
        after,
        last,
        before,
        limit,
        offset,
        base_conditions,
    )

    action_result = await processors.fair_share.search_user_fair_shares.wait_for_complete(
        SearchUserFairSharesAction(
            pagination=querier.pagination,
            conditions=querier.conditions,
            orders=querier.orders,
        )
    )

    nodes = [UserFairShareGQL.from_dataclass(data) for data in action_result.items]
    edges = [UserFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_rg_user_fair_shares(
    info: Info[StrawberryGQLContext],
    scope: UserFairShareSearchScope,
    filter: RGUserFairShareFilter | None = None,
    order_by: list[UserFairShareOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> UserFairShareConnection:
    """Fetch user fair shares using resource group scope.

    Returns all users in the scope, including those without records (with defaults).
    Uses RGUserFairShareFilter whose build_conditions() references INNER JOIN'd
    columns to avoid NULL exclusion.
    """
    processors = info.context.processors
    querier = _build_user_querier(
        get_user_fair_share_pagination_spec(),
        filter,
        order_by,
        first,
        after,
        last,
        before,
        limit,
        offset,
        base_conditions,
    )

    action_result = await processors.fair_share.search_rg_user_fair_shares.wait_for_complete(
        SearchRGUserFairSharesAction(
            scope=scope,
            querier=querier,
        )
    )

    nodes = [UserFairShareGQL.from_dataclass(data) for data in action_result.items]
    edges = [UserFairShareEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return UserFairShareConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=len(action_result.items) > 0 and (first is not None or limit is not None),
            has_previous_page=(offset or 0) > 0 or last is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_single_user_fair_share(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
    project_id: UUID,
    user_uuid: UUID,
) -> UserFairShareGQL:
    """Fetch a single user fair share record.

    Returns the fair share record for the specified user, project, and resource group.
    If no record exists, returns a default-generated object (repository handles defaults).
    """
    processors = info.context.processors

    action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
        GetUserFairShareAction(
            resource_group=resource_group_name,
            project_id=project_id,
            user_uuid=user_uuid,
        )
    )

    return UserFairShareGQL.from_dataclass(action_result.data)
