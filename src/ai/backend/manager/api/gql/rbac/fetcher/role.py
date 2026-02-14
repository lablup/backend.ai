"""Role fetcher functions."""

from __future__ import annotations

import uuid
from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    RoleAssignmentConnection,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleConnection,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
)
from ai.backend.manager.api.gql.rbac.types.role import RoleAssignmentEdge, RoleEdge
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    AssignedUserOrders,
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_roles import (
    SearchRolesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_users_assigned_to_role import (
    SearchUsersAssignedToRoleAction,
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
    action_result = (
        await info.context.processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=id)
        )
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
    base_conditions: list[QueryCondition] | None = None,
) -> RoleConnection:
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
        base_conditions=base_conditions,
    )

    action_result = (
        await info.context.processors.permission_controller.search_roles.wait_for_complete(
            SearchRolesAction(querier=querier)
        )
    )

    result = action_result.result
    edges = [
        RoleEdge(node=RoleGQL.from_dataclass(item), cursor=encode_cursor(str(item.id)))
        for item in result.items
    ]
    return RoleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
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
    base_conditions: list[QueryCondition] | None = None,
) -> RoleAssignmentConnection:
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
        base_conditions=base_conditions,
    )

    action_result = await info.context.processors.permission_controller.search_users_assigned_to_role.wait_for_complete(
        SearchUsersAssignedToRoleAction(querier=querier)
    )

    result = action_result.result
    edges = [
        RoleAssignmentEdge(
            node=RoleAssignmentGQL.from_dataclass(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleAssignmentConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
