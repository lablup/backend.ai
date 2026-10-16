"""GraphQL resolvers for RBAC role management."""

from __future__ import annotations

import uuid
from typing import Annotated

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dto.manager.v2.rbac.request import (
    SearchRoleAssignmentsInput,
    SearchRolesInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types.role import (
    AssignRoleInput,
    BulkAssignRoleInputGQL,
    BulkAssignRolePayloadGQL,
    BulkRevokeRoleInputGQL,
    BulkRevokeRolePayloadGQL,
    CreateRoleInput,
    DeleteRoleInput,
    DeleteRolePayload,
    PartialBulkDeleteRolesInputGQL,
    PartialBulkPurgeRolesInputGQL,
    PartialBulkRestoreRolesInputGQL,
    PartialBulkRolesPayloadGQL,
    PartialBulkUpdateRolesInputGQL,
    PurgeRoleInput,
    PurgeRolePayload,
    RestoreRolePayload,
    RevokeRoleInput,
    RoleAssignmentConnection,
    RoleAssignmentEdge,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleAssignmentOrderBy,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    RoleUsageGQL,
    UpdateRoleInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.rbac_models.role.scopes import (
    ScopedRoleTarget,
)

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
    usage: Annotated[
        RoleUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; roles the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: RoleFilter | None = None,
    order_by: list[RoleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleConnection | None:
    check_admin_only()
    result = await info.context.adapters.rbac.admin_search_roles_gql(
        SearchRolesInput(
            usage=usage.to_pydantic() if usage is not None else None,
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
) -> RoleAssignmentConnection | None:
    check_admin_only()
    result = await info.context.adapters.rbac.admin_search_role_assignments(
        SearchRoleAssignmentsInput(
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
        added_version="26.3.0",
        description=(
            "List the assignment rows joining the current authenticated user to the roles "
            "they hold."
        ),
        deprecated_version="26.9.0",
        deprecation_hint="`myRolesV2`",
    ),
    deprecation_reason=(
        "Deprecated since 26.9.0. Use `myRolesV2`, which answers with the roles themselves."
    ),
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
) -> RoleAssignmentConnection | None:
    me = current_user()
    if me is None:
        from ai.backend.manager.errors.auth import InsufficientPrivilege

        raise InsufficientPrivilege("Authentication required")

    result = await info.context.adapters.rbac.my_search_role_assignments(
        SearchRoleAssignmentsInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
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
        added_version="26.9.0",
        description="List the roles the current authenticated user holds.",
    )
)  # type: ignore[misc]
async def my_roles_v2(
    info: Info[StrawberryGQLContext],
    usage: Annotated[
        RoleUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; roles the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: RoleFilter | None = None,
    order_by: list[RoleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleConnection | None:
    result = await info.context.adapters.rbac.my_search_roles(
        SearchRolesInput(
            usage=usage.to_pydantic() if usage is not None else None,
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
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
        added_version="26.4.2",
        description="List roles registered in a project scope.",
    )
)  # type: ignore[misc]
async def project_roles(
    info: Info[StrawberryGQLContext],
    project_id: uuid.UUID,
    usage: Annotated[
        RoleUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; roles the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: RoleFilter | None = None,
    order_by: list[RoleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleConnection | None:
    result = await info.context.adapters.rbac.search_roles_in_scope(
        [ScopedRoleTarget(scope=ProjectID(project_id))],
        SearchRolesInput(
            usage=usage.to_pydantic() if usage is not None else None,
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
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


# ==================== Mutation Resolvers ====================


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Create a new role (admin only).")
)
async def admin_create_role(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInput,
) -> RoleGQL | None:
    check_admin_only()
    payload = await info.context.adapters.rbac.create(input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Update an existing role (admin only)."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateRole`.",
)
async def admin_update_role(
    info: Info[StrawberryGQLContext],
    input: UpdateRoleInput,
) -> RoleGQL | None:
    check_admin_only()
    if not input.id:
        raise InvalidAPIParameters("`id` is required.")
    payload = await info.context.adapters.rbac.update(input.id, input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Soft-delete a role (admin only)."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `deleteRole`.",
)
async def admin_delete_role(
    info: Info[StrawberryGQLContext],
    input: DeleteRoleInput,
) -> DeleteRolePayload | None:
    check_admin_only()
    result = await info.context.adapters.rbac.delete(input.id)
    return DeleteRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Permanently remove a role (admin only)."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeRole`.",
)
async def admin_purge_role(
    info: Info[StrawberryGQLContext],
    input: PurgeRoleInput,
) -> PurgeRolePayload | None:
    check_admin_only()
    result = await info.context.adapters.rbac.purge(input.id)
    return PurgeRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Assign a role to a user (admin only)."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `assignRole`.",
)
async def admin_assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL | None:
    check_admin_only()
    result = await info.context.adapters.rbac.assign_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Revoke a role from a user (admin only)."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `revokeRole`.",
)
async def admin_revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL | None:
    check_admin_only()
    result = await info.context.adapters.rbac.revoke_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Bulk assign a role to multiple users (admin only)."
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkAssignRoles`.",
)
async def admin_bulk_assign_role(
    info: Info[StrawberryGQLContext],
    input: BulkAssignRoleInputGQL,
) -> BulkAssignRolePayloadGQL | None:
    check_admin_only()
    result = await info.context.adapters.rbac.bulk_assign_role(input.to_pydantic())
    return BulkAssignRolePayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Bulk revoke a role from multiple users (admin only)."
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `partialBulkRevokeRoles`.",
)
async def admin_bulk_revoke_role(
    info: Info[StrawberryGQLContext],
    input: BulkRevokeRoleInputGQL,
) -> BulkRevokeRolePayloadGQL | None:
    check_admin_only()
    result = await info.context.adapters.rbac.bulk_revoke_role(input.to_pydantic())
    return BulkRevokeRolePayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a role. Only provided fields will be updated.",
    )
)
async def update_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
    input: UpdateRoleInput,
) -> RoleGQL:
    payload = await info.context.adapters.rbac.update(id, input.to_pydantic())
    return RoleGQL.from_pydantic(payload.role)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Soft-delete a role.")
)
async def delete_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> DeleteRolePayload:
    result = await info.context.adapters.rbac.delete(id)
    return DeleteRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Restore a soft-deleted role.")
)
async def restore_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> RestoreRolePayload:
    result = await info.context.adapters.rbac.restore(id)
    return RestoreRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Permanently remove a role.")
)
async def purge_role(
    info: Info[StrawberryGQLContext],
    id: uuid.UUID,
) -> PurgeRolePayload:
    result = await info.context.adapters.rbac.purge(id)
    return PurgeRolePayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several roles, answering for each one.",
    )
)
async def partial_bulk_update_roles(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateRolesInputGQL,
) -> PartialBulkRolesPayloadGQL:
    payload = await info.context.adapters.rbac.partial_bulk_update(input.to_pydantic())
    return PartialBulkRolesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete several roles, answering for each one.",
    )
)
async def partial_bulk_delete_roles(
    info: Info[StrawberryGQLContext],
    input: PartialBulkDeleteRolesInputGQL,
) -> PartialBulkRolesPayloadGQL:
    payload = await info.context.adapters.rbac.partial_bulk_delete(input.to_pydantic())
    return PartialBulkRolesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore several soft-deleted roles, answering for each one.",
    )
)
async def partial_bulk_restore_roles(
    info: Info[StrawberryGQLContext],
    input: PartialBulkRestoreRolesInputGQL,
) -> PartialBulkRolesPayloadGQL:
    payload = await info.context.adapters.rbac.partial_bulk_restore(input.to_pydantic())
    return PartialBulkRolesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several roles, answering for each one.",
    )
)
async def partial_bulk_purge_roles(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeRolesInputGQL,
) -> PartialBulkRolesPayloadGQL:
    payload = await info.context.adapters.rbac.partial_bulk_purge(input.to_pydantic())
    return PartialBulkRolesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Assign a role to a user.")
)
async def assign_role(
    info: Info[StrawberryGQLContext],
    input: AssignRoleInput,
) -> RoleAssignmentGQL:
    result = await info.context.adapters.rbac.assign_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Revoke a role from a user.")
)
async def revoke_role(
    info: Info[StrawberryGQLContext],
    input: RevokeRoleInput,
) -> RoleAssignmentGQL:
    result = await info.context.adapters.rbac.revoke_role(input.to_pydantic())
    return RoleAssignmentGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Assign a role to several users, answering for each one.",
    )
)
async def partial_bulk_assign_roles(
    info: Info[StrawberryGQLContext],
    input: BulkAssignRoleInputGQL,
) -> BulkAssignRolePayloadGQL:
    result = await info.context.adapters.rbac.bulk_assign_role(input.to_pydantic())
    return BulkAssignRolePayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Revoke a role from several users, answering for each one.",
    )
)
async def partial_bulk_revoke_roles(
    info: Info[StrawberryGQLContext],
    input: BulkRevokeRoleInputGQL,
) -> BulkRevokeRolePayloadGQL:
    result = await info.context.adapters.rbac.bulk_revoke_role(input.to_pydantic())
    return BulkRevokeRolePayloadGQL.from_pydantic(result)
