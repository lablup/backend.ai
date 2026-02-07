"""GraphQL fetcher for role queries."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    Role,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.services.permission_contoller.actions import (
    GetRoleDetailAction,
    SearchRolesAction,
)


@lru_cache(maxsize=1)
def get_role_pagination_spec() -> PaginationSpec:
    """Get pagination specification for role queries.

    Forward pagination: newest first (created_at DESC)
    Backward pagination: oldest first (created_at ASC, reversed for display)
    """
    return PaginationSpec(
        forward_order=RoleOrders.created_at(ascending=False),
        backward_order=RoleOrders.created_at(ascending=True),
        forward_condition_factory=RoleConditions.by_cursor_forward,
        backward_condition_factory=RoleConditions.by_cursor_backward,
    )


async def fetch_roles(
    info: Info[StrawberryGQLContext],
    filter: RoleFilter | None = None,
    order_by: list[RoleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleConnection:
    """Fetch roles with optional filtering, ordering, and pagination.

    Uses RoleData with deferred resolution for permissions.
    Scope info may not be available in list view - use fetch_role for full details.
    """
    processors = info.context.processors

    # Build querier using gql_adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_role_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.permission_controller.search_roles.wait_for_complete(
        SearchRolesAction(querier=querier)
    )

    # Use RoleData directly - permissions are deferred
    nodes = [Role.from_data(data) for data in action_result.items]
    edges = [RoleEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return RoleConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_role(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
) -> Role:
    """Fetch a specific role by ID with full details.

    Uses GetRoleDetailAction to get scope info.
    Permissions are still deferred for efficiency.
    """
    processors = info.context.processors
    action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    return Role.from_detail_data(action_result.role)
