"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.manager.api.gql.rbac.fetcher.role import (
    fetch_role,
    fetch_role_assignments,
    fetch_roles,
)
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
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions.assign_role import (
    AssignRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.create_role import (
    CreateRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import (
    DeleteRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import (
    PurgeRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import (
    RevokeRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_role import (
    UpdateRoleAction,
)
from ai.backend.manager.types import OptionalState

# ==================== Query Resolvers ====================


@strawberry.field(description="Added in 26.3.0. Get a single role by ID (admin only).")  # type: ignore[misc]
async def admin_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    return await fetch_role(info, id)


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
    return await fetch_role_assignments(
        info,
        filter=filter,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a new role (admin only).")  # type: ignore[misc]
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL:
    action_result = (
        await info.context.processors.permission_controller.create_role.wait_for_complete(
            CreateRoleAction(creator=input.to_creator())
        )
    )
    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Update an existing role (admin only).")  # type: ignore[misc]
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL:
    action_result = (
        await info.context.processors.permission_controller.update_role.wait_for_complete(
            UpdateRoleAction(updater=input.to_updater())
        )
    )
    return RoleGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Soft-delete a role (admin only).")  # type: ignore[misc]
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    input: DeleteRoleInput,
) -> DeleteRolePayload:
    updater = Updater(
        spec=RoleUpdaterSpec(
            status=OptionalState.update(RoleStatus.DELETED),
        ),
        pk_value=input.id,
    )
    await info.context.processors.permission_controller.delete_role.wait_for_complete(
        DeleteRoleAction(updater=updater)
    )
    return DeleteRolePayload(id=ID(str(input.id)))


@strawberry.mutation(description="Added in 26.3.0. Permanently remove a role (admin only).")  # type: ignore[misc]
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    input: PurgeRoleInput,
) -> PurgeRolePayload:
    purger = Purger(row_class=RoleRow, pk_value=input.id)
    await info.context.processors.permission_controller.purge_role.wait_for_complete(
        PurgeRoleAction(purger=purger)
    )
    return PurgeRolePayload(id=ID(str(input.id)))


@strawberry.mutation(description="Added in 26.3.0. Assign a role to a user (admin only).")  # type: ignore[misc]
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    action_result = (
        await info.context.processors.permission_controller.assign_role.wait_for_complete(
            AssignRoleAction(input=input.to_input())
        )
    )
    return RoleAssignmentGQL.from_assignment_data(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Revoke a role from a user (admin only).")  # type: ignore[misc]
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    action_result = (
        await info.context.processors.permission_controller.revoke_role.wait_for_complete(
            RevokeRoleAction(input=input.to_input())
        )
    )
    return RoleAssignmentGQL.from_revocation_data(action_result.data)
