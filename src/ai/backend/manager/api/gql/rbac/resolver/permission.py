"""GraphQL resolvers for RBAC permission management."""

from __future__ import annotations

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.permission.scope_entity_combinations import (
    VALID_SCOPE_ENTITY_COMBINATIONS,
)
from ai.backend.common.data.permission.types import (
    OperationType,
    RBACElementType,
)
from ai.backend.manager.api.gql.rbac.fetcher.permission import fetch_permissions
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
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import PermissionCreatorSpec
from ai.backend.manager.repositories.permission_controller.updaters import PermissionUpdaterSpec
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
)
from ai.backend.manager.types import OptionalState

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
    check_admin_only()
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


@strawberry.field(description="Added in 26.3.0. List valid RBAC scope-entity type combinations.")  # type: ignore[misc]
async def rbac_scope_entity_combinations(
    info: Info[StrawberryGQLContext],
) -> list[ScopeEntityCombinationGQL]:
    return [
        ScopeEntityCombinationGQL(
            scope_type=RBACElementTypeGQL.from_element(scope),
            valid_entity_types=sorted(
                [RBACElementTypeGQL.from_element(entity) for entity in entities],
                key=lambda e: e.value,
            ),
        )
        for scope, entities in VALID_SCOPE_ENTITY_COMBINATIONS.items()
    ]


# ==================== Mutation Resolvers ====================


@strawberry.mutation(description="Added in 26.3.0. Create a scoped permission (admin only).")  # type: ignore[misc]
async def admin_create_permission(
    info: Info[StrawberryGQLContext],
    input: CreatePermissionInput,
) -> PermissionGQL:
    check_admin_only()
    dto = input.to_pydantic()
    creator = Creator(
        spec=PermissionCreatorSpec(
            role_id=dto.role_id,
            scope_type=RBACElementType(dto.scope_type).to_scope_type(),
            scope_id=dto.scope_id,
            entity_type=RBACElementType(dto.entity_type).to_entity_type(),
            operation=OperationType(dto.operation),
        )
    )
    action_result = (
        await info.context.processors.permission_controller.create_permission.wait_for_complete(
            CreatePermissionAction(creator=creator)
        )
    )
    return PermissionGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Update a scoped permission (admin only).")  # type: ignore[misc]
async def admin_update_permission(
    info: Info[StrawberryGQLContext],
    input: UpdatePermissionInput,
) -> PermissionGQL:
    check_admin_only()
    dto = input.to_pydantic()
    spec = PermissionUpdaterSpec(
        scope_type=(
            OptionalState.update(RBACElementType(dto.scope_type).to_scope_type())
            if dto.scope_type is not None
            else OptionalState.nop()
        ),
        scope_id=(
            OptionalState.update(dto.scope_id) if dto.scope_id is not None else OptionalState.nop()
        ),
        entity_type=(
            OptionalState.update(RBACElementType(dto.entity_type).to_entity_type())
            if dto.entity_type is not None
            else OptionalState.nop()
        ),
        operation=(
            OptionalState.update(OperationType(dto.operation))
            if dto.operation is not None
            else OptionalState.nop()
        ),
    )
    action_result = (
        await info.context.processors.permission_controller.update_permission.wait_for_complete(
            UpdatePermissionAction(updater=Updater(spec=spec, pk_value=dto.id))
        )
    )
    return PermissionGQL.from_dataclass(action_result.data)


@strawberry.mutation(description="Added in 26.3.0. Delete a scoped permission (admin only).")  # type: ignore[misc]
async def admin_delete_permission(
    info: Info[StrawberryGQLContext],
    input: DeletePermissionInput,
) -> DeletePermissionPayload:
    check_admin_only()
    purger = Purger(row_class=PermissionRow, pk_value=input.id)
    await info.context.processors.permission_controller.delete_permission.wait_for_complete(
        DeletePermissionAction(purger=purger)
    )
    return DeletePermissionPayload(id=ID(str(input.id)))
