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
from ai.backend.manager.api.gql.rbac.types.permission import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
)
from ai.backend.manager.api.gql.rbac.types.scope import (
    Scope,
    ScopeConnection,
    ScopeEdge,
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
) -> Optional[Role]:
    """Fetch a specific role by ID."""
    processors = info.context.processors
    action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    if action_result.role is None:
        return None

    return Role.from_detail_data(action_result.role)


async def fetch_role_scopes(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
) -> ScopeConnection:
    """Fetch scopes (permission groups) for a specific role."""
    processors = info.context.processors
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    scopes = [Scope.from_permission_group(pg) for pg in detail_result.role.permission_groups]
    edges = [ScopeEdge(node=scope, cursor=encode_cursor(str(scope.id))) for scope in scopes]

    return ScopeConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=len(scopes),
    )


async def fetch_role_object_permissions(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
) -> ObjectPermissionConnection:
    """Fetch object permissions for a specific role."""
    processors = info.context.processors
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    perms = [ObjectPermission.from_dataclass(op) for op in detail_result.role.object_permissions]
    edges = [ObjectPermissionEdge(node=perm, cursor=encode_cursor(str(perm.id))) for perm in perms]

    return ObjectPermissionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=len(perms),
    )


async def fetch_scope_permissions(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    scope_id: str,
) -> ScopedPermissionConnection:
    """Fetch scoped permissions for a specific scope within a role."""
    processors = info.context.processors
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    # Find the matching permission group
    permissions = []
    for pg in detail_result.role.permission_groups:
        if pg.scope_id.scope_id == scope_id:
            permissions = [ScopedPermission.from_dataclass(p) for p in pg.permissions]
            break

    edges = [
        ScopedPermissionEdge(node=perm, cursor=encode_cursor(str(perm.id))) for perm in permissions
    ]

    return ScopedPermissionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=len(permissions),
    )
