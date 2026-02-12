"""Role fetcher functions."""

from __future__ import annotations

import uuid
from functools import lru_cache

from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.api.gql.rbac.types import (
    RoleAssignmentConnection,
    RoleAssignmentFilter,
    RoleConnection,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
)
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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
