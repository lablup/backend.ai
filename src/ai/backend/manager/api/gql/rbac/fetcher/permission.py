"""GraphQL fetcher for permission queries."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    PermissionGroup,
    PermissionGroupConnection,
    PermissionGroupEdge,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.permission_controller.options import (
    ObjectPermissionConditions,
    ObjectPermissionOrders,
    PermissionGroupConditions,
    PermissionGroupOrders,
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)
from ai.backend.manager.repositories.permission_controller.types import (
    ObjectPermissionSearchScope,
    PermissionGroupSearchScope,
    ScopedPermissionSearchScope,
)
from ai.backend.manager.services.permission_contoller.actions import (
    SearchObjectPermissionsAction,
    SearchPermissionGroupsAction,
    SearchScopedPermissionsAction,
)


@lru_cache(maxsize=1)
def get_scoped_permission_pagination_spec() -> PaginationSpec:
    """Get pagination specification for scoped permission queries."""
    return PaginationSpec(
        forward_order=ScopedPermissionOrders.id(ascending=False),
        backward_order=ScopedPermissionOrders.id(ascending=True),
        forward_condition_factory=ScopedPermissionConditions.by_cursor_forward,
        backward_condition_factory=ScopedPermissionConditions.by_cursor_backward,
    )


@lru_cache(maxsize=1)
def get_object_permission_pagination_spec() -> PaginationSpec:
    """Get pagination specification for object permission queries."""
    return PaginationSpec(
        forward_order=ObjectPermissionOrders.id(ascending=False),
        backward_order=ObjectPermissionOrders.id(ascending=True),
        forward_condition_factory=ObjectPermissionConditions.by_cursor_forward,
        backward_condition_factory=ObjectPermissionConditions.by_cursor_backward,
    )


async def fetch_role_scoped_permissions(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ScopedPermissionConnection:
    """Fetch scoped permissions for a role with pagination."""
    processors = info.context.processors

    scope = ScopedPermissionSearchScope(role_id=role_id)

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_scoped_permission_pagination_spec(),
    )

    action_result = (
        await processors.permission_controller.search_scoped_permissions.wait_for_complete(
            SearchScopedPermissionsAction(querier=querier, scope=scope)
        )
    )

    nodes = [ScopedPermission.from_data(data) for data in action_result.items]
    edges = [ScopedPermissionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ScopedPermissionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_role_object_permissions(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ObjectPermissionConnection:
    """Fetch object permissions for a role with pagination."""
    processors = info.context.processors

    scope = ObjectPermissionSearchScope(role_id=role_id)

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_object_permission_pagination_spec(),
    )

    action_result = (
        await processors.permission_controller.search_object_permissions.wait_for_complete(
            SearchObjectPermissionsAction(querier=querier, scope=scope)
        )
    )

    nodes = [ObjectPermission.from_dataclass(data) for data in action_result.items]
    edges = [ObjectPermissionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ObjectPermissionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@lru_cache(maxsize=1)
def get_permission_group_pagination_spec() -> PaginationSpec:
    """Get pagination specification for permission group queries."""
    return PaginationSpec(
        forward_order=PermissionGroupOrders.id(ascending=False),
        backward_order=PermissionGroupOrders.id(ascending=True),
        forward_condition_factory=PermissionGroupConditions.by_cursor_forward,
        backward_condition_factory=PermissionGroupConditions.by_cursor_backward,
    )


async def fetch_role_permission_groups(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PermissionGroupConnection:
    """Fetch permission groups for a role with pagination."""
    processors = info.context.processors

    scope = PermissionGroupSearchScope(role_id=role_id)

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_permission_group_pagination_spec(),
    )

    action_result = (
        await processors.permission_controller.search_permission_groups.wait_for_complete(
            SearchPermissionGroupsAction(querier=querier, scope=scope)
        )
    )

    nodes = [PermissionGroup.from_data(data) for data in action_result.items]
    edges = [PermissionGroupEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return PermissionGroupConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
