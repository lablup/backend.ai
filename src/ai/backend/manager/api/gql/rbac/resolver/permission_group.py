"""GraphQL query resolvers for permission group management."""

from __future__ import annotations

import logging

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.fetcher import fetch_permission_groups
from ai.backend.manager.api.gql.rbac.types import (
    PermissionGroupConnection,
    PermissionGroupFilter,
    PermissionGroupOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

log = logging.getLogger(__spec__.name)


# ==============================================================================
# Query Resolvers
# ==============================================================================


@strawberry.field(description="List permission groups with optional filtering and pagination")  # type: ignore[misc]
async def admin_permission_groups(
    info: Info[StrawberryGQLContext],
    filter: PermissionGroupFilter | None = None,
    order_by: list[PermissionGroupOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PermissionGroupConnection:
    """List all permission groups with filtering, ordering, and pagination.

    Permission groups represent scopes (domain, project, user) that have
    permissions assigned within a role.
    """
    check_admin_only()
    return await fetch_permission_groups(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
