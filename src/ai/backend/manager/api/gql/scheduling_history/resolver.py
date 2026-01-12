"""GraphQL query resolvers for scheduling history."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    DeploymentHistoryOrders,
    RouteHistoryConditions,
    RouteHistoryOrders,
    SessionSchedulingHistoryConditions,
    SessionSchedulingHistoryOrders,
)
from ai.backend.manager.services.scheduling_history.actions import (
    SearchDeploymentHistoryAction,
    SearchRouteHistoryAction,
    SearchSessionHistoryAction,
)

from .types import (
    DeploymentHistory,
    DeploymentHistoryFilter,
    DeploymentHistoryOrderBy,
    RouteHistory,
    RouteHistoryFilter,
    RouteHistoryOrderBy,
    SessionSchedulingHistory,
    SessionSchedulingHistoryFilter,
    SessionSchedulingHistoryOrderBy,
)

# Pagination specs


@lru_cache(maxsize=1)
def _get_session_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=SessionSchedulingHistoryOrders.created_at(ascending=False),
        backward_order=SessionSchedulingHistoryOrders.created_at(ascending=True),
        forward_condition_factory=SessionSchedulingHistoryConditions.by_cursor_forward,
        backward_condition_factory=SessionSchedulingHistoryConditions.by_cursor_backward,
    )


@lru_cache(maxsize=1)
def _get_deployment_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentHistoryOrders.created_at(ascending=False),
        backward_order=DeploymentHistoryOrders.created_at(ascending=True),
        forward_condition_factory=DeploymentHistoryConditions.by_cursor_forward,
        backward_condition_factory=DeploymentHistoryConditions.by_cursor_backward,
    )


@lru_cache(maxsize=1)
def _get_route_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteHistoryOrders.created_at(ascending=False),
        backward_order=RouteHistoryOrders.created_at(ascending=True),
        forward_condition_factory=RouteHistoryConditions.by_cursor_forward,
        backward_condition_factory=RouteHistoryConditions.by_cursor_backward,
    )


# Connection types

SessionSchedulingHistoryEdge = Edge[SessionSchedulingHistory]


@strawberry.type(description="Session scheduling history connection")
class SessionSchedulingHistoryConnection(Connection[SessionSchedulingHistory]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


DeploymentHistoryEdge = Edge[DeploymentHistory]


@strawberry.type(description="Deployment history connection")
class DeploymentHistoryConnection(Connection[DeploymentHistory]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


RouteHistoryEdge = Edge[RouteHistory]


@strawberry.type(description="Route history connection")
class RouteHistoryConnection(Connection[RouteHistory]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="List session scheduling history (superadmin only)")
async def session_scheduling_histories(
    info: Info[StrawberryGQLContext],
    filter: Optional[SessionSchedulingHistoryFilter] = None,
    order_by: Optional[list[SessionSchedulingHistoryOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> SessionSchedulingHistoryConnection:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")

    processors = info.context.processors

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_session_history_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scheduling_history.search_session_history.wait_for_complete(
        SearchSessionHistoryAction(querier=querier)
    )

    nodes = [SessionSchedulingHistory.from_dataclass(data) for data in action_result.histories]

    edges = [
        SessionSchedulingHistoryEdge(node=node, cursor=encode_cursor(str(node.id)))
        for node in nodes
    ]

    return SessionSchedulingHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(description="List deployment history (superadmin only)")
async def deployment_histories(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentHistoryFilter] = None,
    order_by: Optional[list[DeploymentHistoryOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> DeploymentHistoryConnection:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")

    processors = info.context.processors

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_deployment_history_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scheduling_history.search_deployment_history.wait_for_complete(
        SearchDeploymentHistoryAction(querier=querier)
    )

    nodes = [DeploymentHistory.from_dataclass(data) for data in action_result.histories]

    edges = [DeploymentHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return DeploymentHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(description="List route history (superadmin only)")
async def route_histories(
    info: Info[StrawberryGQLContext],
    filter: Optional[RouteHistoryFilter] = None,
    order_by: Optional[list[RouteHistoryOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> RouteHistoryConnection:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")

    processors = info.context.processors

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_route_history_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.scheduling_history.search_route_history.wait_for_complete(
        SearchRouteHistoryAction(querier=querier)
    )

    nodes = [RouteHistory.from_dataclass(data) for data in action_result.histories]

    edges = [RouteHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return RouteHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
