"""GraphQL fetcher for role queries."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
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
    filter: Optional[RoleFilter] = None,
    order_by: Optional[list[RoleOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> RoleConnection:
    """Fetch roles with optional filtering, ordering, and pagination."""
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

    # Convert RoleData to RoleDetailData by fetching details for each role
    roles_with_details = []
    for role_data in action_result.items:
        detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=role_data.id)
        )
        if detail_result.role:
            roles_with_details.append(detail_result.role)

    nodes = [Role.from_dataclass(data) for data in roles_with_details]
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
) -> Optional[Role]:
    """Fetch a specific role by ID."""
    processors = info.context.processors
    action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    if action_result.role is None:
        return None

    return Role.from_dataclass(action_result.role)
