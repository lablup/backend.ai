"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.types import (
    AssignRoleInput,
    CreateRoleInput,
    DeleteRoleInput,
    DeleteRolePayload,
    PurgeRoleInput,
    PurgeRolePayload,
    RevokeRoleInput,
    RoleAssignmentConnection,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleConnection,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    UpdateRoleInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# ==================== Query Resolvers ====================


@strawberry.field(description="Added in 26.3.0. Get a single role by ID (admin only).")  # type: ignore[misc]
async def admin_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    raise NotImplementedError


@strawberry.field(
    description="Added in 26.3.0. List roles with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_roles(
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
    raise NotImplementedError


@strawberry.field(
    description="Added in 26.3.0. List role assignments with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_role_assignments(
    info: Info[StrawberryGQLContext],
    filter: RoleAssignmentFilter | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleAssignmentConnection:
    raise NotImplementedError


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a new role (admin only).")  # type: ignore[misc]
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Update an existing role (admin only).")  # type: ignore[misc]
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Soft-delete a role (admin only).")  # type: ignore[misc]
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    input: DeleteRoleInput,
) -> DeleteRolePayload:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Permanently remove a role (admin only).")  # type: ignore[misc]
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    input: PurgeRoleInput,
) -> PurgeRolePayload:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Assign a role to a user (admin only).")  # type: ignore[misc]
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    raise NotImplementedError


@strawberry.mutation(description="Added in 26.3.0. Revoke a role from a user (admin only).")  # type: ignore[misc]
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    raise NotImplementedError
