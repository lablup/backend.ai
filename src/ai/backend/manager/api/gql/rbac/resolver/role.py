"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.permission.types import RoleStatus
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchRoleAssignmentsGQLInput,
    AdminSearchRolesGQLInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.rbac.types import (
    AssignRoleInput,
    BulkAssignRoleErrorGQL,
    BulkAssignRoleInputGQL,
    BulkAssignRolePayloadGQL,
    BulkRevokeRoleErrorGQL,
    BulkRevokeRoleInputGQL,
    BulkRevokeRolePayloadGQL,
    CreateRoleInput,
    DeleteRoleInput,
    DeleteRolePayload,
    PurgeRoleInput,
    PurgeRolePayload,
    RevokeRoleInput,
    RoleAssignmentConnection,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleAssignmentOrderBy,
    RoleConnection,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    UpdateRoleInput,
)
from ai.backend.manager.api.gql.rbac.types.role import RoleAssignmentEdge, RoleEdge
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.permission.role import (
    BulkUserRoleRevocationInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.models.rbac_models.conditions import AssignedUserConditions
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions.assign_role import (
    AssignRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_revoke_role import (
    BulkRevokeRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.delete_role import (
    DeleteRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_role_detail import (
    GetRoleDetailAction,
)
from ai.backend.manager.services.permission_contoller.actions.purge_role import (
    PurgeRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import (
    RevokeRoleAction,
)
from ai.backend.manager.types import OptionalState


async def _fetch_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    action_result = (
        await info.context.processors.permission_controller.get_role_detail.wait_for_complete(
            GetRoleDetailAction(role_id=id)
        )
    )
    return RoleGQL.from_dataclass(action_result.role)


async def _fetch_roles(
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
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

    search_input = AdminSearchRolesGQLInput(
        filter=pydantic_filter,
        order=pydantic_order,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.rbac.admin_search_roles_gql(
        search_input,
        base_conditions=base_conditions,
    )

    edges = [
        RoleEdge(node=RoleGQL.from_dataclass(item), cursor=encode_cursor(str(item.id)))
        for item in result.items
    ]
    return RoleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


async def _fetch_role_assignments(
    info: Info[StrawberryGQLContext],
    filter: RoleAssignmentFilter | None = None,
    order_by: list[RoleAssignmentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> RoleAssignmentConnection:
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

    search_input = AdminSearchRoleAssignmentsGQLInput(
        filter=pydantic_filter,
        order=pydantic_order,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.rbac.admin_search_role_assignments_gql(
        search_input,
        base_conditions=base_conditions,
    )

    edges = [
        RoleAssignmentEdge(
            node=RoleAssignmentGQL.from_dataclass(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleAssignmentConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


# ==================== Query Resolvers ====================


@strawberry.field(description="Added in 26.3.0. Get a single role by ID (admin only).")  # type: ignore[misc]
async def admin_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    check_admin_only()
    return await _fetch_role(info, id)


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
    check_admin_only()
    return await _fetch_roles(
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
    order_by: list[RoleAssignmentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleAssignmentConnection:
    check_admin_only()
    return await _fetch_role_assignments(
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
    description="Added in 26.3.0. List roles assigned to the current authenticated user.",
)  # type: ignore[misc]
async def my_roles(
    info: Info[StrawberryGQLContext],
    filter: RoleAssignmentFilter | None = None,
    order_by: list[RoleAssignmentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleAssignmentConnection:
    me = current_user()
    if me is None:
        from ai.backend.manager.errors.auth import InsufficientPrivilege

        raise InsufficientPrivilege("Authentication required")

    return await _fetch_role_assignments(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
        base_conditions=[AssignedUserConditions.by_user_id(me.user_id)],
    )


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a new role (admin only).")  # type: ignore[misc]
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL:
    check_admin_only()
    payload = await info.context.adapters.rbac.create(input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@strawberry.mutation(description="Added in 26.3.0. Update an existing role (admin only).")  # type: ignore[misc]
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL:
    check_admin_only()
    payload = await info.context.adapters.rbac.update(input.id, input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@strawberry.mutation(description="Added in 26.3.0. Soft-delete a role (admin only).")  # type: ignore[misc]
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    input: DeleteRoleInput,
) -> DeleteRolePayload:
    check_admin_only()
    updater = Updater(
        spec=RoleUpdaterSpec(
            status=OptionalState.update(RoleStatus.DELETED),
        ),
        pk_value=input.id,
    )
    await info.context.processors.permission_controller.delete_role.wait_for_complete(
        DeleteRoleAction(updater=updater)
    )
    return DeleteRolePayload(id=input.id)


@strawberry.mutation(description="Added in 26.3.0. Permanently remove a role (admin only).")  # type: ignore[misc]
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    input: PurgeRoleInput,
) -> PurgeRolePayload:
    check_admin_only()
    purger = Purger(row_class=RoleRow, pk_value=input.id)
    await info.context.processors.permission_controller.purge_role.wait_for_complete(
        PurgeRoleAction(purger=purger)
    )
    return PurgeRolePayload(id=input.id)


@strawberry.mutation(description="Added in 26.3.0. Assign a role to a user (admin only).")  # type: ignore[misc]
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()
    dto = input.to_pydantic()
    action_result = (
        await info.context.processors.permission_controller.assign_role.wait_for_complete(
            AssignRoleAction(
                input=UserRoleAssignmentInput(user_id=dto.user_id, role_id=dto.role_id)
            )
        )
    )
    return RoleAssignmentGQL.from_assignment_data(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Revoke a role from a user (admin only).")  # type: ignore[misc]
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()
    dto = input.to_pydantic()
    action_result = (
        await info.context.processors.permission_controller.revoke_role.wait_for_complete(
            RevokeRoleAction(
                input=UserRoleRevocationInput(user_id=dto.user_id, role_id=dto.role_id)
            )
        )
    )
    return RoleAssignmentGQL.from_revocation_data(action_result.data)


@strawberry.mutation(
    description="Added in 26.3.0. Bulk assign a role to multiple users (admin only)."
)  # type: ignore[misc]
async def admin_bulk_assign_role(
    info: Info[StrawberryGQLContext],
    input: BulkAssignRoleInputGQL,
) -> BulkAssignRolePayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    specs = [UserRoleCreatorSpec(user_id=uid, role_id=dto.role_id) for uid in dto.user_ids]
    action_result = (
        await info.context.processors.permission_controller.bulk_assign_role.wait_for_complete(
            BulkAssignRoleAction(bulk_creator=BulkCreator(specs=specs))
        )
    )
    return BulkAssignRolePayloadGQL(
        assigned=[RoleAssignmentGQL.from_assignment_data(s) for s in action_result.data.successes],
        failed=[
            BulkAssignRoleErrorGQL(user_id=f.user_id, message=f.message)
            for f in action_result.data.failures
        ],
    )


@strawberry.mutation(
    description="Added in 26.3.0. Bulk revoke a role from multiple users (admin only)."
)  # type: ignore[misc]
async def admin_bulk_revoke_role(
    info: Info[StrawberryGQLContext],
    input: BulkRevokeRoleInputGQL,
) -> BulkRevokeRolePayloadGQL:
    check_admin_only()
    dto = input.to_pydantic()
    action_result = (
        await info.context.processors.permission_controller.bulk_revoke_role.wait_for_complete(
            BulkRevokeRoleAction(
                input=BulkUserRoleRevocationInput(role_id=dto.role_id, user_ids=dto.user_ids)
            )
        )
    )
    return BulkRevokeRolePayloadGQL(
        revoked=[RoleAssignmentGQL.from_revocation_data(s) for s in action_result.data.successes],
        failed=[
            BulkRevokeRoleErrorGQL(user_id=f.user_id, message=f.message)
            for f in action_result.data.failures
        ],
    )
