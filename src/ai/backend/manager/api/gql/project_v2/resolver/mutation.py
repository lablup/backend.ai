"""Project V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dto.manager.v2.group.request import PurgeProjectInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.project_v2.types.mutations import (
    CreateProjectInputGQL,
    DeleteProjectPayloadGQL,
    PartialBulkDeleteProjectsInputGQL,
    PartialBulkProjectsPayloadGQL,
    PartialBulkRestoreProjectsInputGQL,
    PartialBulkUpdateProjectsInputGQL,
    ProjectPayloadGQL,
    PurgeProjectPayloadGQL,
    RestoreProjectPayloadGQL,
    UnassignUsersFromProjectInputGQL,
    UnassignUsersFromProjectPayloadGQL,
    UpdateProjectInputGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new project (admin only). Requires superadmin privileges.",
    )
)
async def admin_create_project_v2(
    info: Info[StrawberryGQLContext],
    input: CreateProjectInputGQL,
) -> ProjectPayloadGQL | None:
    """Create a new project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_create(input.to_pydantic())
    return ProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a project. Only provided fields will be updated.",
    )
)
async def update_project_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateProjectInputGQL,
) -> ProjectPayloadGQL:
    payload = await info.context.adapters.project.update(ProjectID(id), input.to_pydantic())
    return ProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Soft-delete a project.")
)
async def delete_project_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteProjectPayloadGQL:
    payload = await info.context.adapters.project.delete(ProjectID(id))
    return DeleteProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Restore a soft-deleted project."
    )
)
async def restore_project_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RestoreProjectPayloadGQL:
    payload = await info.context.adapters.project.restore(ProjectID(id))
    return RestoreProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several projects, answering for each one.",
    )
)
async def partial_bulk_update_projects_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateProjectsInputGQL,
) -> PartialBulkProjectsPayloadGQL:
    payload = await info.context.adapters.project.partial_bulk_update(input.to_pydantic())
    return PartialBulkProjectsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete several projects, answering for each one.",
    )
)
async def partial_bulk_delete_projects_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkDeleteProjectsInputGQL,
) -> PartialBulkProjectsPayloadGQL:
    payload = await info.context.adapters.project.partial_bulk_delete(input.to_pydantic())
    return PartialBulkProjectsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore several soft-deleted projects, answering for each one.",
    )
)
async def partial_bulk_restore_projects_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkRestoreProjectsInputGQL,
) -> PartialBulkProjectsPayloadGQL:
    payload = await info.context.adapters.project.partial_bulk_restore(input.to_pydantic())
    return PartialBulkProjectsPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a project (admin only). Requires superadmin privileges. Only provided fields will be updated.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateProjectV2`.",
)
async def admin_update_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    input: UpdateProjectInputGQL,
) -> ProjectPayloadGQL | None:
    """Update a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.update(ProjectID(project_id), input.to_pydantic())
    return ProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Soft-delete a project (admin only). Requires superadmin privileges.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `deleteProjectV2`.",
)
async def admin_delete_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> DeleteProjectPayloadGQL | None:
    """Soft-delete a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.delete(ProjectID(project_id))
    return DeleteProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description="Restore a soft-deleted project (admin only). Requires superadmin privileges.",
    ),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `restoreProjectV2`.",
)
async def admin_restore_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> RestoreProjectPayloadGQL | None:
    """Restore a soft-deleted project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.restore(ProjectID(project_id))
    return RestoreProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Permanently purge a project and all associated data (admin only). Requires superadmin privileges.",
    )
)
async def admin_purge_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> PurgeProjectPayloadGQL | None:
    """Permanently purge a project."""
    check_admin_only()
    ctx = info.context
    payload = await ctx.adapters.project.admin_purge(PurgeProjectInput(group_id=project_id))
    return PurgeProjectPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Unassign users from a project. RBAC validates project admin permission.",
    )
)
async def unassign_users_from_project_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    input: UnassignUsersFromProjectInputGQL,
) -> UnassignUsersFromProjectPayloadGQL | None:
    """Unassign users from a project."""
    ctx = info.context
    payload = await ctx.adapters.project.unassign_users(project_id, input.to_pydantic())
    return UnassignUsersFromProjectPayloadGQL.from_pydantic(payload)
