"""GraphQL query and mutation resolvers for role management."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

import strawberry
from strawberry import ID, Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.rbac import RoleStatus
from ai.backend.manager.api.gql.rbac.fetcher import fetch_role, fetch_roles
from ai.backend.manager.api.gql.rbac.types import (
    CreateRoleAssignmentInput,
    CreateRoleInput,
    Role,
    RoleConnection,
    RoleFilter,
    RoleOrderBy,
    UpdateRoleInput,
    UpdateRolePermissionsInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.permission.role import (
    RolePermissionsUpdateInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions import (
    AssignRoleAction,
    CreateRoleAction,
    DeleteRoleAction,
    GetRoleDetailAction,
    PurgeRoleAction,
    RevokeRoleAction,
    UpdateRoleAction,
    UpdateRolePermissionsAction,
)
from ai.backend.manager.types import OptionalState

log = logging.getLogger(__spec__.name)  # type: ignore[name-defined]


# ==============================================================================
# Query Resolvers
# ==============================================================================


@strawberry.field(description="Get a specific role by ID")
async def role(id: ID, info: Info[StrawberryGQLContext]) -> Optional[Role]:
    """Get a single role with full details."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can access role details")

    return await fetch_role(info, role_id=uuid.UUID(id))


@strawberry.field(description="List roles with optional filtering and pagination")
async def roles(
    info: Info[StrawberryGQLContext],
    filter: Optional[RoleFilter] = None,
    order_by: Optional[list[RoleOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> RoleConnection:
    """List roles with filtering, ordering, and pagination."""
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can list roles")

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


@strawberry.field(description="Create a new custom role")
async def create_role(input: CreateRoleInput, info: Info[StrawberryGQLContext]) -> Role:
    """Create a new custom role.

    Requires: Superadmin permission.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can create roles")

    processors = info.context.processors

    creator = input.to_creator()

    action_result = await processors.permission_controller.create_role.wait_for_complete(
        CreateRoleAction(creator=creator)
    )

    # Fetch full details
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=action_result.data.id)
    )

    return Role.from_dataclass(detail_result.role)


@strawberry.field(description="Update an existing role")
async def update_role(input: UpdateRoleInput, info: Info[StrawberryGQLContext]) -> Role:
    """Update a role's name and/or description.

    Requires: Superadmin permission.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can update roles")

    processors = info.context.processors

    updater = input.to_updater()

    action_result = await processors.permission_controller.update_role.wait_for_complete(
        UpdateRoleAction(updater=updater)
    )

    # Fetch full details
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=action_result.data.id)
    )

    return Role.from_dataclass(detail_result.role)


@strawberry.field(description="Delete a role (soft delete)")
async def delete_role(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Soft-delete a role.

    Requires: Superadmin permission.
    System roles cannot be deleted.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can delete roles")

    processors = info.context.processors
    rold_id = uuid.UUID(id)

    # Get role details before deletion
    detail_result_before = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=rold_id)
    )

    # Delete role
    spec = RoleUpdaterSpec(
        status=OptionalState.update(RoleStatus.DELETED),
    )
    updater = Updater(spec=spec, pk_value=rold_id)
    await processors.permission_controller.delete_role.wait_for_complete(
        DeleteRoleAction(updater=updater)
    )

    # Return the deleted role (with original data)
    return Role.from_dataclass(detail_result_before.role)


@strawberry.field(description="Delete a role (soft delete)")
async def purge_role(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Purge a role.

    Requires: Superadmin permission.
    System roles cannot be deleted.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can delete roles")

    processors = info.context.processors
    rold_id = uuid.UUID(id)

    # Get role details before deletion
    detail_result_before = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=rold_id)
    )

    # Delete role
    purger = Purger(row_class=RoleRow, pk_value=rold_id)
    await processors.permission_controller.purge_role.wait_for_complete(
        PurgeRoleAction(purger=purger)
    )

    # Return the deleted role (with original data)
    return Role.from_dataclass(detail_result_before.role)


@strawberry.field(description="Update role permissions")
async def update_role_permissions(
    input: UpdateRolePermissionsInput, info: Info[StrawberryGQLContext]
) -> Role:
    """Update role permissions by removing specified permissions.

    Requires: Superadmin permission.

    Note: Currently only supports permission deletion. Permission addition
    should be done during role creation or through separate mutations.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can update role permissions")

    processors = info.context.processors

    # Build RolePermissionsUpdateInput for deletion only
    input_data = RolePermissionsUpdateInput(
        role_id=uuid.UUID(input.role_id),
        remove_scoped_permission_ids=[
            uuid.UUID(id) for id in (input.scoped_permission_ids_to_delete or [])
        ],
        remove_object_permission_ids=[
            uuid.UUID(id) for id in (input.object_permission_ids_to_delete or [])
        ],
    )

    # Update permissions
    action_result = (
        await processors.permission_controller.update_role_permissions.wait_for_complete(
            UpdateRolePermissionsAction(input_data=input_data)
        )
    )

    return Role.from_dataclass(action_result.role)


@strawberry.field(description="Assign a role to a user")
async def create_role_assignment(
    input: CreateRoleAssignmentInput, info: Info[StrawberryGQLContext]
) -> Role:
    """Assign a role to a user in a specific scope.

    Requires: Superadmin permission.

    Returns the role that was assigned (not a RoleAssignment object,
    since we don't have RoleAssignment type in this implementation).
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can assign roles")

    processors = info.context.processors

    # Create assignment input
    assignment_input = UserRoleAssignmentInput(
        user_id=uuid.UUID(input.user_id),
        role_id=uuid.UUID(input.role_id),
        granted_by=me.user_id if me and me.user_id else None,
    )

    await processors.permission_controller.assign_role.wait_for_complete(
        AssignRoleAction(input=assignment_input)
    )

    # Return the assigned role
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=uuid.UUID(input.role_id))
    )

    return Role.from_dataclass(detail_result.role)


@strawberry.field(description="Revoke a role assignment")
async def delete_role_assignment(id: ID, info: Info[StrawberryGQLContext]) -> Role:
    """Revoke a role assignment (remove role from user).

    Requires: Superadmin permission.

    NOTE: The 'id' parameter should be formatted as 'user_id:role_id' since we don't
    have a separate RoleAssignment entity with its own ID in the current implementation.

    Returns the role that was revoked.
    """
    me = current_user()
    if me is None or not me.is_superadmin:
        raise NotEnoughPermission("Only superadmin can revoke role assignments")

    processors = info.context.processors

    # Parse the composite ID (format: "user_id:role_id")
    try:
        user_id_str, role_id_str = str(id).split(":", 1)
        user_id = uuid.UUID(user_id_str)
        role_id = uuid.UUID(role_id_str)
    except (ValueError, AttributeError) as e:
        raise ValueError(
            f"Invalid role assignment ID format: {id}. Expected 'user_id:role_id'"
        ) from e

    # Get role details before revocation
    detail_result = await processors.permission_controller.get_role_detail.wait_for_complete(
        GetRoleDetailAction(role_id=role_id)
    )

    # Revoke assignment
    revocation_input = UserRoleRevocationInput(
        user_id=user_id,
        role_id=role_id,
    )

    await processors.permission_controller.revoke_role.wait_for_complete(
        RevokeRoleAction(input=revocation_input)
    )

    # Return the revoked role
    return Role.from_dataclass(detail_result.role)
