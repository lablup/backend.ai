"""GraphQL adapter for RBAC queries."""

from __future__ import annotations

from functools import lru_cache

from ai.backend.manager.api.gql.adapter import PaginationSpec
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
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
