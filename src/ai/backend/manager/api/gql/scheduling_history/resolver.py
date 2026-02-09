"""GraphQL query resolvers for scheduling history."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
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
    SearchDeploymentScopedHistoryAction,
    SearchRouteHistoryAction,
    SearchRouteScopedHistoryAction,
    SearchSessionHistoryAction,
    SearchSessionScopedHistoryAction,
)

from .types import (
    DeploymentHistory,
    DeploymentHistoryFilter,
    DeploymentHistoryOrderBy,
    DeploymentScope,
    RouteHistory,
    RouteHistoryFilter,
    RouteHistoryOrderBy,
    RouteScope,
    SessionSchedulingHistory,
    SessionSchedulingHistoryFilter,
    SessionSchedulingHistoryOrderBy,
    SessionScope,
)

# Pagination specs


@lru_cache(maxsize=1)
def _get_session_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=SessionSchedulingHistoryOrders.created_at(ascending=False),
        backward_order=SessionSchedulingHistoryOrders.created_at(ascending=True),
        forward_condition_factory=SessionSchedulingHistoryConditions.by_cursor_forward,
        backward_condition_factory=SessionSchedulingHistoryConditions.by_cursor_backward,
        tiebreaker_order=SessionSchedulingHistoryRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_deployment_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentHistoryOrders.created_at(ascending=False),
        backward_order=DeploymentHistoryOrders.created_at(ascending=True),
        forward_condition_factory=DeploymentHistoryConditions.by_cursor_forward,
        backward_condition_factory=DeploymentHistoryConditions.by_cursor_backward,
        tiebreaker_order=DeploymentHistoryRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_route_history_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RouteHistoryOrders.created_at(ascending=False),
        backward_order=RouteHistoryOrders.created_at(ascending=True),
        forward_condition_factory=RouteHistoryConditions.by_cursor_forward,
        backward_condition_factory=RouteHistoryConditions.by_cursor_backward,
        tiebreaker_order=RouteHistoryRow.id.asc(),
    )


# Connection types

SessionSchedulingHistoryEdge = Edge[SessionSchedulingHistory]


@strawberry.type(description="Session scheduling history connection")
class SessionSchedulingHistoryConnection(Connection[SessionSchedulingHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


DeploymentHistoryEdge = Edge[DeploymentHistory]


@strawberry.type(description="Deployment history connection")
class DeploymentHistoryConnection(Connection[DeploymentHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


RouteHistoryEdge = Edge[RouteHistory]


@strawberry.type(description="Route history connection")
class RouteHistoryConnection(Connection[RouteHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Helper functions for scoped queries


async def fetch_session_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: SessionScope,
    filter: SessionSchedulingHistoryFilter | None = None,
    order_by: list[SessionSchedulingHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionSchedulingHistoryConnection:
    """Shared logic for fetching session-scoped scheduling histories.

    Used by session_scoped_scheduling_histories query resolver.
    """
    from ai.backend.manager.repositories.scheduling_history.types import (
        SessionSchedulingHistorySearchScope,
    )

    processors = info.context.processors

    # Build querier from filter (scope is passed separately to action)
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

    # Convert GraphQL scope to repository scope
    repo_scope = SessionSchedulingHistorySearchScope(session_id=scope.session_id)

    # Use scoped action
    action_result = (
        await processors.scheduling_history.search_session_scoped_history.wait_for_complete(
            SearchSessionScopedHistoryAction(querier=querier, scope=repo_scope)
        )
    )

    # Build connection
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


async def fetch_deployment_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: DeploymentScope,
    filter: DeploymentHistoryFilter | None = None,
    order_by: list[DeploymentHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DeploymentHistoryConnection:
    """Shared logic for fetching deployment-scoped scheduling histories.

    Used by deployment_scoped_scheduling_histories query resolver.
    """
    from ai.backend.manager.repositories.scheduling_history.types import (
        DeploymentHistorySearchScope,
    )

    processors = info.context.processors

    # Build querier from filter (scope is passed separately to action)
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

    # Convert GraphQL scope to repository scope
    repo_scope = DeploymentHistorySearchScope(deployment_id=scope.deployment_id)

    # Use scoped action
    action_result = (
        await processors.scheduling_history.search_deployment_scoped_history.wait_for_complete(
            SearchDeploymentScopedHistoryAction(querier=querier, scope=repo_scope)
        )
    )

    # Build connection
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


async def fetch_route_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: RouteScope,
    filter: RouteHistoryFilter | None = None,
    order_by: list[RouteHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RouteHistoryConnection:
    """Shared logic for fetching route-scoped scheduling histories.

    Used by route_scoped_scheduling_histories query resolver.
    """
    from ai.backend.manager.repositories.scheduling_history.types import RouteHistorySearchScope

    processors = info.context.processors

    # Build querier from filter (scope is passed separately to action)
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

    # Convert GraphQL scope to repository scope
    repo_scope = RouteHistorySearchScope(route_id=scope.route_id)

    # Use scoped action
    action_result = (
        await processors.scheduling_history.search_route_scoped_history.wait_for_complete(
            SearchRouteScopedHistoryAction(querier=querier, scope=repo_scope)
        )
    )

    # Build connection
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


# Query fields


@strawberry.field(description="List session scheduling history (admin only)")  # type: ignore[misc]
async def admin_session_scheduling_histories(
    info: Info[StrawberryGQLContext],
    filter: SessionSchedulingHistoryFilter | None = None,
    order_by: list[SessionSchedulingHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionSchedulingHistoryConnection:
    check_admin_only()

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


@strawberry.field(  # type: ignore[misc]
    description="List session scheduling history (superadmin only)",
    deprecation_reason=(
        "Use admin_session_scheduling_histories instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def session_scheduling_histories(
    info: Info[StrawberryGQLContext],
    filter: SessionSchedulingHistoryFilter | None = None,
    order_by: list[SessionSchedulingHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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


@strawberry.field(description="List deployment history (admin only)")  # type: ignore[misc]
async def admin_deployment_histories(
    info: Info[StrawberryGQLContext],
    filter: DeploymentHistoryFilter | None = None,
    order_by: list[DeploymentHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DeploymentHistoryConnection:
    check_admin_only()

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


@strawberry.field(  # type: ignore[misc]
    description="List deployment history (superadmin only)",
    deprecation_reason=(
        "Use admin_deployment_histories instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def deployment_histories(
    info: Info[StrawberryGQLContext],
    filter: DeploymentHistoryFilter | None = None,
    order_by: list[DeploymentHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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


@strawberry.field(description="List route history (admin only)")  # type: ignore[misc]
async def admin_route_histories(
    info: Info[StrawberryGQLContext],
    filter: RouteHistoryFilter | None = None,
    order_by: list[RouteHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RouteHistoryConnection:
    check_admin_only()

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


@strawberry.field(  # type: ignore[misc]
    description="List route history (superadmin only)",
    deprecation_reason=(
        "Use admin_route_histories instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def route_histories(
    info: Info[StrawberryGQLContext],
    filter: RouteHistoryFilter | None = None,
    order_by: list[RouteHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
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


# Scoped query fields (added in 26.2.0)


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. Get scheduling history for a specific session."
)
async def session_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: SessionScope,
    filter: SessionSchedulingHistoryFilter | None = None,
    order_by: list[SessionSchedulingHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionSchedulingHistoryConnection:
    """Get scheduling history for a specific session.

    Returns all scheduling history records for the specified session.
    Permission checking is handled by RBAC.
    """
    return await fetch_session_scoped_scheduling_histories(
        info=info,
        scope=scope,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. Get scheduling history for a specific deployment."
)
async def deployment_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: DeploymentScope,
    filter: DeploymentHistoryFilter | None = None,
    order_by: list[DeploymentHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DeploymentHistoryConnection:
    """Get scheduling history for a specific deployment.

    Returns all scheduling history records for the specified deployment.
    Permission checking is handled by RBAC.
    """
    return await fetch_deployment_scoped_scheduling_histories(
        info=info,
        scope=scope,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(  # type: ignore[misc]
    description="Added in 26.2.0. Get scheduling history for a specific route."
)
async def route_scoped_scheduling_histories(
    info: Info[StrawberryGQLContext],
    scope: RouteScope,
    filter: RouteHistoryFilter | None = None,
    order_by: list[RouteHistoryOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RouteHistoryConnection:
    """Get scheduling history for a specific route.

    Returns all scheduling history records for the specified route.
    Permission checking is handled by RBAC.
    """
    return await fetch_route_scoped_scheduling_histories(
        info=info,
        scope=scope,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
