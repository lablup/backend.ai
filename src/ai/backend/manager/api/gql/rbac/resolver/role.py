"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.rbac.fetcher import (
    fetch_role,
    fetch_role_assignments,
    fetch_roles,
)
from ai.backend.manager.api.gql.rbac.types import (
    AssignRoleInput,
    CreateRoleInput,
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
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.permission.status import RoleStatus
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
)
from ai.backend.manager.types import OptionalState

# ==================== Query Resolvers ====================


@strawberry.field(description="Added in 26.2.0. Get a single role by ID (admin only).")  # type: ignore[misc]
async def admin_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    check_admin_only()
    return await fetch_role(info, id)


@strawberry.field(
    description="Added in 26.2.0. List roles with filtering and pagination (admin only)."
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
    check_admin_only()
    return await fetch_roles(
        info=info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(
    description="Added in 26.2.0. List role assignments with filtering and pagination (admin only)."
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
    check_admin_only()
    return await fetch_role_assignments(
        info=info,
        filter=filter,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.2.0. Create a new role (admin only).")  # type: ignore[misc]
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.create_role.wait_for_complete(
        CreateRoleAction(creator=input.to_creator(), object_permissions=[])
    )

    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.2.0. Update an existing role (admin only).")  # type: ignore[misc]
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.update_role.wait_for_complete(
        UpdateRoleAction(updater=input.to_updater())
    )

    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.2.0. Soft-delete a role (admin only).")  # type: ignore[misc]
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.delete_role.wait_for_complete(
        DeleteRoleAction(
            updater=Updater(
                spec=RoleUpdaterSpec(status=OptionalState.update(RoleStatus.DELETED)),
                pk_value=id,
            ),
        )
    )

    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.2.0. Permanently remove a role (admin only).")  # type: ignore[misc]
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.purge_role.wait_for_complete(
        PurgeRoleAction(purger=Purger(row_class=RoleRow, pk_value=id))
    )

    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.2.0. Assign a role to a user (admin only).")  # type: ignore[misc]
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.assign_role.wait_for_complete(
        AssignRoleAction(input=input.to_input())
    )

    return RoleAssignmentGQL.from_assignment_data(action_result.data)


@strawberry.mutation(description="Added in 26.2.0. Revoke a role from a user (admin only).")  # type: ignore[misc]
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()

    processors = info.context.processors
    action_result = await processors.permission_controller.revoke_role.wait_for_complete(
        RevokeRoleAction(input=input.to_input())
    )

    return RoleAssignmentGQL.from_revocation_data(action_result.data)
