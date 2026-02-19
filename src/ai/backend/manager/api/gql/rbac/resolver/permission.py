"""GraphQL resolvers for RBAC permission management."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.types import (
    CreatePermissionInput,
    DeletePermissionInput,
    DeletePermissionPayload,
    PermissionConnection,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    RBACElementTypeGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# ==================== Query Resolvers ====================


@strawberry.field(
    description="Added in 26.3.0. List scoped permissions with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_permissions(
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


@strawberry.field(
    description="Added in 26.3.0. List available scope types.",
    deprecation_reason="Deprecated since 26.3.0. Use RBACElementType enum values directly.",
)  # type: ignore[misc]
async def scope_types(
    info: Info[StrawberryGQLContext],
) -> list[RBACElementTypeGQL]:
    raise NotImplementedError


@strawberry.field(
    description="Added in 26.3.0. List available entity types.",
    deprecation_reason="Deprecated since 26.3.0. Use RBACElementType enum values directly.",
)  # type: ignore[misc]
async def entity_types(
    info: Info[StrawberryGQLContext],
) -> list[RBACElementTypeGQL]:
    raise NotImplementedError


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a scoped permission (admin only).")  # type: ignore[misc]
async def admin_create_permission(
    info: Info[StrawberryGQLContext],
    input: CreatePermissionInput,
) -> PermissionGQL:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Delete a scoped permission (admin only).")  # type: ignore[misc]
async def admin_delete_permission(
    info: Info[StrawberryGQLContext],
    input: DeletePermissionInput,
) -> DeletePermissionPayload:
    raise NotImplementedError
