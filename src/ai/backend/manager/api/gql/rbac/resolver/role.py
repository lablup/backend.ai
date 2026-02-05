"""GraphQL query and mutation resolvers for role management."""

from __future__ import annotations

import logging
import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import RoleStatus
from ai.backend.manager.api.gql.rbac.fetcher import fetch_role, fetch_roles
from ai.backend.manager.api.gql.rbac.types import (
    CreateRoleAssignmentInput,
    CreateRoleInput,
    DeleteRoleAssignmentInput,
    Role,
    RoleConnection,
    RoleFilter,
    RoleOrderBy,
    UpdateRoleInput,
    UpdateRolePermissionsInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.permission.role import (
    RolePermissionsUpdateInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions import (
    AssignRoleAction,
    CreateRoleAction,
    DeleteRoleAction,
    PurgeRoleAction,
    RevokeRoleAction,
    UpdateRoleAction,
    UpdateRolePermissionsAction,
)
from ai.backend.manager.types import OptionalState

log = logging.getLogger(__spec__.name)


# ==============================================================================
# Query Resolvers
# ==============================================================================


@strawberry.field(description="Get a specific role by ID")  # type: ignore[misc]
async def admin_role(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Get a single role with full details."""
    check_admin_only()
    return await fetch_role(info, role_id=uuid.UUID(id))


@strawberry.field(description="List roles with optional filtering and pagination")  # type: ignore[misc]
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
    """List roles with filtering, ordering, and pagination."""
    check_admin_only()
    return await fetch_roles(
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


# ==============================================================================
# Mutation Resolvers
# ==============================================================================


@strawberry.field(description="Create a new custom role")  # type: ignore[misc]
async def admin_create_role(input: CreateRoleInput, info: Info[StrawberryGQLContext]) -> Role:
    """Create a new custom role.

    Requires: Superadmin permission.
    """
    check_admin_only()
    processors = info.context.processors

    creator = input.to_creator()

    action_result = await processors.permission_controller.create_role.wait_for_complete(
        CreateRoleAction(creator=creator)
    )

    return Role.from_data(action_result.data)


@strawberry.field(description="Update an existing role")  # type: ignore[misc]
async def admin_update_role(input: UpdateRoleInput, info: Info[StrawberryGQLContext]) -> Role:
    """Update a role's name and/or description.

    Requires: Superadmin permission.
    """
    check_admin_only()
    processors = info.context.processors

    updater = input.to_updater()

    action_result = await processors.permission_controller.update_role.wait_for_complete(
        UpdateRoleAction(updater=updater)
    )

    return Role.from_data(action_result.data)


@strawberry.field(description="Delete a role (soft delete)")  # type: ignore[misc]
async def admin_delete_role(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Soft-delete a role.

    Requires: Superadmin permission.
    System roles cannot be deleted.
    """
    check_admin_only()
    processors = info.context.processors
    role_id = uuid.UUID(id)

    spec = RoleUpdaterSpec(
        status=OptionalState.update(RoleStatus.DELETED),
    )
    updater = Updater(spec=spec, pk_value=role_id)
    result = await processors.permission_controller.delete_role.wait_for_complete(
        DeleteRoleAction(updater=updater)
    )

    return Role.from_data(result.data)


@strawberry.field(description="Purge a role (hard delete)")  # type: ignore[misc]
async def admin_purge_role(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Purge a role.

    Requires: Superadmin permission.
    System roles cannot be deleted.
    """
    check_admin_only()
    processors = info.context.processors
    role_id = uuid.UUID(id)

    purger = Purger(row_class=RoleRow, pk_value=role_id)
    result = await processors.permission_controller.purge_role.wait_for_complete(
        PurgeRoleAction(purger=purger)
    )

    return Role.from_data(result.data)


@strawberry.field(description="Update role permissions")  # type: ignore[misc]
async def admin_update_role_permissions(
    input: UpdateRolePermissionsInput, info: Info[StrawberryGQLContext]
) -> Role:
    """Update role permissions by removing specified permissions.

    Requires: Superadmin permission.

    Note: Currently only supports permission deletion. Permission addition
    should be done during role creation or through separate mutations.
    """
    check_admin_only()
    processors = info.context.processors

    input_data = RolePermissionsUpdateInput(
        role_id=uuid.UUID(input.role_id),
        remove_scoped_permission_ids=[
            uuid.UUID(id) for id in (input.scoped_permission_ids_to_delete or [])
        ],
        remove_object_permission_ids=[
            uuid.UUID(id) for id in (input.object_permission_ids_to_delete or [])
        ],
    )

    action_result = (
        await processors.permission_controller.update_role_permissions.wait_for_complete(
            UpdateRolePermissionsAction(input_data=input_data)
        )
    )

    return Role.from_detail_data(action_result.role)


@strawberry.field(description="Assign a role to a user")  # type: ignore[misc]
async def admin_create_role_assignment(
    input: CreateRoleAssignmentInput, info: Info[StrawberryGQLContext]
) -> Role:
    """Assign a role to a user in a specific scope.

    Requires: Superadmin permission.

    Returns the role that was assigned (not a RoleAssignment object,
    since we don't have RoleAssignment type in this implementation).
    """
    check_admin_only()
    me = current_user()
    processors = info.context.processors

    assignment_input = UserRoleAssignmentInput(
        user_id=uuid.UUID(input.user_id),
        role_id=uuid.UUID(input.role_id),
        granted_by=me.user_id if me else None,
    )

    result = await processors.permission_controller.assign_role.wait_for_complete(
        AssignRoleAction(input=assignment_input)
    )

    return Role.from_data(result.data.role)


@strawberry.field(description="Revoke a role assignment")  # type: ignore[misc]
async def admin_delete_role_assignment(
    input: DeleteRoleAssignmentInput,
    info: Info[StrawberryGQLContext],
) -> Role:
    """Revoke a role assignment (remove role from user).

    Requires: Superadmin permission.

    Returns the role that was revoked.
    """
    check_admin_only()
    processors = info.context.processors

    revocation_input = UserRoleRevocationInput(
        user_id=uuid.UUID(input.user_id),
        role_id=uuid.UUID(input.role_id),
    )

    result = await processors.permission_controller.revoke_role.wait_for_complete(
        RevokeRoleAction(input=revocation_input)
    )

    return Role.from_data(result.data.role)
