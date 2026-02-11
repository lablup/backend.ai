"""Role fetcher functions."""

from __future__ import annotations

import uuid
from functools import lru_cache

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    RoleAssignmentConnection,
    RoleAssignmentEdge,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    AssignedUserOrders,
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.services.permission_contoller.actions import (
    SearchRolesAction,
    SearchUsersAssignedToRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)


@lru_cache(maxsize=1)
def get_role_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RoleOrders.created_at(ascending=False),
        backward_order=RoleOrders.created_at(ascending=True),
        forward_condition_factory=RoleConditions.by_cursor_forward,
        backward_condition_factory=RoleConditions.by_cursor_backward,
        tiebreaker_order=RoleRow.id.asc(),
    )


@lru_cache(maxsize=1)
def get_role_assignment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AssignedUserOrders.granted_at(ascending=False),
        backward_order=AssignedUserOrders.granted_at(ascending=True),
        forward_condition_factory=AssignedUserConditions.by_cursor_forward,
        backward_condition_factory=AssignedUserConditions.by_cursor_backward,
        tiebreaker_order=UserRoleRow.id.asc(),
    )


async def fetch_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    processors = info.context.processors
    action_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=id)
    )
    return RoleGQL.from_dataclass(action_result.role)


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
        get_role_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.permission_controller.search_roles.wait_for_complete(
        SearchRolesAction(querier=querier)
    )

    nodes = [RoleGQL.from_dataclass(data) for data in action_result.items]
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


async def fetch_role_assignments(
    info: Info[StrawberryGQLContext],
    filter: RoleAssignmentFilter | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleAssignmentConnection:
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
        get_role_assignment_pagination_spec(),
        filter=filter,
    )

    action_result = (
        await processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
            SearchUsersAssignedToRoleAction(querier=querier)
        )
    )

    nodes = [RoleAssignmentGQL.from_dataclass(data) for data in action_result.items]
    edges = [RoleAssignmentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return RoleAssignmentConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
