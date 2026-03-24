"""GraphQL resolvers for RBAC permission management."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.data.permission.scope_entity_combinations import (
    VALID_SCOPE_ENTITY_COMBINATIONS,
)
from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchPermissionsGQLInput
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types import (
    CreatePermissionInput,
    DeletePermissionInput,
    DeletePermissionPayload,
    PermissionConnection,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    RBACElementTypeGQL,
    ScopeEntityCombinationGQL,
    UpdatePermissionInput,
)
from ai.backend.manager.api.gql.rbac.types.permission import PermissionEdge
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# ==================== Query Resolvers ====================


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="List scoped permissions with filtering and pagination (admin only).",
    )
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
    check_admin_only()
    result = await info.context.adapters.rbac.admin_search_permissions_gql(
        AdminSearchPermissionsGQLInput(
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
        PermissionEdge(
            node=PermissionGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return PermissionConnection(
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
        added_version="26.3.0", description="List valid RBAC scope-entity type combinations."
    )
)  # type: ignore[misc]
async def rbac_scope_entity_combinations(
    info: Info[StrawberryGQLContext],
) -> list[ScopeEntityCombinationGQL]:
    return [
        ScopeEntityCombinationGQL(
            scope_type=RBACElementTypeGQL(scope.value),
            valid_entity_types=sorted(
                [RBACElementTypeGQL(entity.value) for entity in entities],
                key=lambda e: e.value,  # type: ignore[attr-defined]
            ),
        )
        for scope, entities in VALID_SCOPE_ENTITY_COMBINATIONS.items()
    ]


# ==================== Mutation Resolvers ====================


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Create a scoped permission (admin only).")
)  # type: ignore[misc]
async def admin_create_permission(
    info: Info[StrawberryGQLContext],
    input: CreatePermissionInput,
) -> PermissionGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.create_permission(input.to_pydantic())
    return PermissionGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Update a scoped permission (admin only).")
)  # type: ignore[misc]
async def admin_update_permission(
    info: Info[StrawberryGQLContext],
    input: UpdatePermissionInput,
) -> PermissionGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.update_permission(input.to_pydantic())
    return PermissionGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(added_version="26.3.0", description="Delete a scoped permission (admin only).")
)  # type: ignore[misc]
async def admin_delete_permission(
    info: Info[StrawberryGQLContext],
    input: DeletePermissionInput,
) -> DeletePermissionPayload:
    check_admin_only()
    result = await info.context.adapters.rbac.delete_permission(input.id)
    return DeletePermissionPayload.from_pydantic(result)
