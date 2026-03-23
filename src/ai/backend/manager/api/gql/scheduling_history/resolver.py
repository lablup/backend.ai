"""GraphQL query resolvers for scheduling history."""

from __future__ import annotations

from typing import Any

import strawberry
from aiohttp import web
from strawberry import Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_connection_type
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

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

# Connection types


SessionSchedulingHistoryEdge = Edge[SessionSchedulingHistory]


@gql_connection_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Session scheduling history connection.")
)
class SessionSchedulingHistoryConnection(Connection[SessionSchedulingHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


DeploymentHistoryEdge = Edge[DeploymentHistory]


@gql_connection_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Deployment history connection.")
)
class DeploymentHistoryConnection(Connection[DeploymentHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


RouteHistoryEdge = Edge[RouteHistory]


@gql_connection_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Route history connection.")
)
class RouteHistoryConnection(Connection[RouteHistory]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


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
) -> SessionSchedulingHistoryConnection | None:
    check_admin_only()
    result = await info.context.adapters.scheduling_history.admin_search_session_history(
        AdminSearchSessionHistoriesInput(
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
    nodes = [SessionSchedulingHistory.from_pydantic(item) for item in result.items]
    edges = [
        SessionSchedulingHistoryEdge(node=node, cursor=encode_cursor(str(node.id)))
        for node in nodes
    ]
    return SessionSchedulingHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> SessionSchedulingHistoryConnection | None:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")
    result = await info.context.adapters.scheduling_history.admin_search_session_history(
        AdminSearchSessionHistoriesInput(
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
    nodes = [SessionSchedulingHistory.from_pydantic(item) for item in result.items]
    edges = [
        SessionSchedulingHistoryEdge(node=node, cursor=encode_cursor(str(node.id)))
        for node in nodes
    ]
    return SessionSchedulingHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> DeploymentHistoryConnection | None:
    check_admin_only()
    result = await info.context.adapters.scheduling_history.admin_search_deployment_history(
        AdminSearchDeploymentHistoriesInput(
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
    nodes = [DeploymentHistory.from_pydantic(item) for item in result.items]
    edges = [DeploymentHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DeploymentHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> DeploymentHistoryConnection | None:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")
    result = await info.context.adapters.scheduling_history.admin_search_deployment_history(
        AdminSearchDeploymentHistoriesInput(
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
    nodes = [DeploymentHistory.from_pydantic(item) for item in result.items]
    edges = [DeploymentHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DeploymentHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> RouteHistoryConnection | None:
    check_admin_only()
    result = await info.context.adapters.scheduling_history.admin_search_route_history(
        AdminSearchRouteHistoriesInput(
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
    nodes = [RouteHistory.from_pydantic(item) for item in result.items]
    edges = [RouteHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return RouteHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> RouteHistoryConnection | None:
    me = current_user()
    if me is None or not me.is_superadmin:
        raise web.HTTPForbidden(reason="Only superadmin can access scheduling history.")
    result = await info.context.adapters.scheduling_history.admin_search_route_history(
        AdminSearchRouteHistoriesInput(
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
    nodes = [RouteHistory.from_pydantic(item) for item in result.items]
    edges = [RouteHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return RouteHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> SessionSchedulingHistoryConnection | None:
    """Get scheduling history for a specific session."""
    result = await info.context.adapters.scheduling_history.session_scoped_search(
        scope.session_id,
        AdminSearchSessionHistoriesInput(
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
    nodes = [SessionSchedulingHistory.from_pydantic(item) for item in result.items]
    edges = [
        SessionSchedulingHistoryEdge(node=node, cursor=encode_cursor(str(node.id)))
        for node in nodes
    ]
    return SessionSchedulingHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> DeploymentHistoryConnection | None:
    """Get scheduling history for a specific deployment."""
    result = await info.context.adapters.scheduling_history.deployment_scoped_search(
        scope.deployment_id,
        AdminSearchDeploymentHistoriesInput(
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
    nodes = [DeploymentHistory.from_pydantic(item) for item in result.items]
    edges = [DeploymentHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return DeploymentHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
) -> RouteHistoryConnection | None:
    """Get scheduling history for a specific route."""
    result = await info.context.adapters.scheduling_history.route_scoped_search(
        scope.route_id,
        AdminSearchRouteHistoriesInput(
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
    nodes = [RouteHistory.from_pydantic(item) for item in result.items]
    edges = [RouteHistoryEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return RouteHistoryConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
