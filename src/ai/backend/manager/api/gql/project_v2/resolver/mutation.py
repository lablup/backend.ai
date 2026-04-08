"""Project V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.dto.manager.v2.group.request import DeleteProjectInput, PurgeProjectInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.project_v2.types.mutations import (
    CreateProjectInputGQL,
    DeleteProjectPayloadGQL,
    ProjectPayloadGQL,
    PurgeProjectPayloadGQL,
    UnassignUsersFromProjectInputGQL,
    UnassignUsersFromProjectPayloadGQL,
    UpdateProjectInputGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new project (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_create_project_v2(
    info: Info[StrawberryGQLContext],
    input: CreateProjectInputGQL,
) -> ProjectPayloadGQL:
    """Create a new project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_create(input.to_pydantic())
    return ProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a project (admin only). Requires superadmin privileges. Only provided fields will be updated.",
    )
)  # type: ignore[misc]
async def admin_update_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    input: UpdateProjectInputGQL,
) -> ProjectPayloadGQL:
    """Update a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_update(project_id, input.to_pydantic())
    return ProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete a project (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_delete_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> DeleteProjectPayloadGQL:
    """Soft-delete a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_delete(DeleteProjectInput(group_id=project_id))
    return DeleteProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently purge a project and all associated data (admin only). Requires superadmin privileges.",
    )
)  # type: ignore[misc]
async def admin_purge_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> PurgeProjectPayloadGQL:
    """Permanently purge a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_purge(PurgeProjectInput(group_id=project_id))
    return PurgeProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Unassign users from a project. RBAC validates project admin permission.",
    )
)  # type: ignore[misc]
async def unassign_users_from_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    input: UnassignUsersFromProjectInputGQL,
) -> UnassignUsersFromProjectPayloadGQL:
    """Unassign users from a project."""
    ctx = info.context
    payload = await ctx.adapters.project.unassign_users(project_id, input.to_pydantic())
    return UnassignUsersFromProjectPayloadGQL.from_pydantic(payload)
