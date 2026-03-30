"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.rbac.request import (
    AdminSearchRoleAssignmentsGQLInput,
    AdminSearchRolesGQLInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types import (
    AssignRoleInput,
    BulkAssignRoleInputGQL,
    BulkAssignRolePayloadGQL,
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
from ai.backend.manager.models.rbac_models.conditions import AssignedUserConditions

# ==================== Query Resolvers ====================


@gql_root_field(
    BackendAIGQLMeta(added_version="26.3.0", description="Get a single role by ID (admin only).")
)  # type: ignore[misc]
async def admin_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RoleGQL | None:
    check_admin_only()
    node = await info.context.adapters.rbac.get(id)
    return RoleGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0", description="List roles with filtering and pagination (admin only)."
    )
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
    result = await info.context.adapters.rbac.admin_search_roles_gql(
        AdminSearchRolesGQLInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    edges = [
        RoleEdge(node=RoleGQL.from_pydantic(item), cursor=encode_cursor(str(item.id)))
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="List role assignments with filtering and pagination (admin only).",
    )
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
    result = await info.context.adapters.rbac.admin_search_role_assignments_gql(
        AdminSearchRoleAssignmentsGQLInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    edges = [
        RoleAssignmentEdge(
            node=RoleAssignmentGQL.from_pydantic(item),
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0", description="List roles assigned to the current authenticated user."
    )
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

    result = await info.context.adapters.rbac.admin_search_role_assignments_gql(
        AdminSearchRoleAssignmentsGQLInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        base_conditions=[AssignedUserConditions.by_user_id(me.user_id)],
    )
    edges = [
        RoleAssignmentEdge(
            node=RoleAssignmentGQL.from_pydantic(item),
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


# ==================== Mutation Resolvers ====================


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Create a new role (admin only).")
)  # type: ignore[misc]
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL:
    check_admin_only()
    payload = await info.context.adapters.rbac.create(input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Update an existing role (admin only).")
)  # type: ignore[misc]
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL:
    check_admin_only()
    payload = await info.context.adapters.rbac.update(input.id, input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Soft-delete a role (admin only).")
)  # type: ignore[misc]
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    input: DeleteRoleInput,
) -> DeleteRolePayload:
    check_admin_only()
    result = await info.context.adapters.rbac.delete(input.id)
    return DeleteRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Permanently remove a role (admin only).")
)  # type: ignore[misc]
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    input: PurgeRoleInput,
) -> PurgeRolePayload:
    check_admin_only()
    result = await info.context.adapters.rbac.purge(input.id)
    return PurgeRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Assign a role to a user (admin only).")
)  # type: ignore[misc]
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.assign_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Revoke a role from a user (admin only).")
)  # type: ignore[misc]
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.revoke_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Bulk assign a role to multiple users (admin only)."
    )
)  # type: ignore[misc]
async def admin_bulk_assign_role(
    info: Info[StrawberryGQLContext],
    input: BulkAssignRoleInputGQL,
) -> BulkAssignRolePayloadGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.bulk_assign_role(input.to_pydantic())
    return BulkAssignRolePayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Bulk revoke a role from multiple users (admin only)."
    )
)  # type: ignore[misc]
async def admin_bulk_revoke_role(
    info: Info[StrawberryGQLContext],
    input: BulkRevokeRoleInputGQL,
) -> BulkRevokeRolePayloadGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.bulk_revoke_role(input.to_pydantic())
    return BulkRevokeRolePayloadGQL.from_pydantic(result)
