"""GraphQL resolvers for RBAC permission management."""

from __future__ import annotations

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.rbac.fetcher.permission import fetch_permissions
from ai.backend.manager.api.gql.rbac.types import (
    CreatePermissionInput,
    DeletePermissionInput,
    DeletePermissionPayload,
    EntityTypeGQL,
    PermissionConnection,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.permission_contoller.actions.get_entity_types import (
    GetEntityTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)

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
    return await fetch_permissions(
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


@strawberry.field(description="Added in 26.3.0. List available scope types.")  # type: ignore[misc]
async def scope_types(
    info: Info[StrawberryGQLContext],
) -> list[EntityTypeGQL]:
    action_result = (
        await info.context.processors.permission_controller.get_scope_types.wait_for_complete(
            GetScopeTypesAction()
        )
    )
    return [EntityTypeGQL.from_scope_type(st) for st in action_result.scope_types]


@strawberry.field(description="Added in 26.3.0. List available entity types.")  # type: ignore[misc]
async def entity_types(
    info: Info[StrawberryGQLContext],
) -> list[EntityTypeGQL]:
    action_result = (
        await info.context.processors.permission_controller.get_entity_types.wait_for_complete(
            GetEntityTypesAction()
        )
    )
    return [EntityTypeGQL.from_internal(et) for et in action_result.entity_types]


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a scoped permission (admin only).")  # type: ignore[misc]
async def admin_create_permission(
    info: Info[StrawberryGQLContext],
    input: CreatePermissionInput,
) -> PermissionGQL:
    action_result = (
        await info.context.processors.permission_controller.create_permission.wait_for_complete(
            CreatePermissionAction(creator=input.to_creator())
        )
    )
    return PermissionGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Delete a scoped permission (admin only).")  # type: ignore[misc]
async def admin_delete_permission(
    info: Info[StrawberryGQLContext],
    input: DeletePermissionInput,
) -> DeletePermissionPayload:
    purger = Purger(row_class=PermissionRow, pk_value=input.id)
    await info.context.processors.permission_controller.delete_permission.wait_for_complete(
        DeletePermissionAction(purger=purger)
    )
    return DeletePermissionPayload(id=ID(str(input.id)))
