"""Permission fetcher functions."""

from __future__ import annotations

from functools import lru_cache

from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.api.gql.rbac.types import (
    PermissionConnection,
    PermissionFilter,
    PermissionOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.permission_controller.options import (
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)


@lru_cache(maxsize=1)
def get_permission_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ScopedPermissionOrders.id(ascending=False),
        backward_order=ScopedPermissionOrders.id(ascending=True),
        forward_condition_factory=ScopedPermissionConditions.by_cursor_forward,
        backward_condition_factory=ScopedPermissionConditions.by_cursor_backward,
        tiebreaker_order=PermissionRow.id.asc(),
    )


async def fetch_permissions(
    info: Info[StrawberryGQLContext],
    filter: PermissionFilter | None = None,
    order_by: list[PermissionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PermissionConnection:
    raise NotImplementedError
