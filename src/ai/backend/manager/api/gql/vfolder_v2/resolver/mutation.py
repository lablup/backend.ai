"""VFolder GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.dto.manager.v2.vfolder.request import (
    PurgeVFolderInput,
    PurgeVFolderOptions,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_v2.types.mutations import (
    BulkDeleteVFoldersInputGQL,
    BulkDeleteVFoldersPayloadGQL,
    BulkPurgeVFoldersInputGQL,
    BulkPurgeVFoldersPayloadGQL,
    CloneVFolderInputGQL,
    CloneVFolderPayloadGQL,
    CreateVFolderInputGQL,
    CreateVFolderInScopeInputGQL,
    CreateVFolderPayloadGQL,
    DeleteFilesInputGQL,
    DeleteFilesPayloadGQL,
    DeleteVFolderPayloadGQL,
    DeployVFolderInputGQL,
    DeployVFolderPayloadGQL,
    DownloadSessionInputGQL,
    DownloadSessionPayloadGQL,
    ListFilesInputGQL,
    ListFilesPayloadGQL,
    MkdirInputGQL,
    MkdirPayloadGQL,
    MoveFileInputGQL,
    MoveFilePayloadGQL,
    PurgeVFolderOptionsInputGQL,
    PurgeVFolderPayloadGQL,
    RestoreVFolderOptionsInputGQL,
    RestoreVFolderPayloadGQL,
    UploadSessionInputGQL,
    UploadSessionPayloadGQL,
)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new virtual folder.",
    )
)
async def create_vfolder_v2(
    info: Info[StrawberryGQLContext],
    input: CreateVFolderInputGQL,
) -> CreateVFolderPayloadGQL | None:
    payload = await info.context.adapters.vfolder.create(input.to_pydantic())
    return CreateVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Soft-delete a virtual folder (move to trash).",
    )
)
async def delete_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
) -> DeleteVFolderPayloadGQL | None:
    payload = await info.context.adapters.vfolder.delete(vfolder_id)
    return DeleteVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Permanently purge a virtual folder.",
    )
)
async def purge_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    options: PurgeVFolderOptionsInputGQL | None = None,
) -> PurgeVFolderPayloadGQL | None:
    options_dto = options.to_pydantic() if options is not None else PurgeVFolderOptions()
    payload = await info.context.adapters.vfolder.purge(
        vfolder_id,
        PurgeVFolderInput(options=options_dto),
    )
    return PurgeVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Restore a trashed virtual folder. RBAC enforced via scope chain.",
    ),
    name="restoreVFolder",
)
async def restore_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    options: RestoreVFolderOptionsInputGQL | None = None,
) -> RestoreVFolderPayloadGQL | None:
    """Restore a virtual folder from trash."""
    owner_id = options.to_pydantic().owner_id if options is not None else None
    payload = await info.context.adapters.vfolder.restore(vfolder_id, owner_id=owner_id)
    return RestoreVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Deploy a deployment directly from a model VFolder.",
    )
)
async def deploy_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: DeployVFolderInputGQL,
) -> DeployVFolderPayloadGQL | None:
    payload = await info.context.adapters.vfolder.deploy(vfolder_id, input.to_pydantic())
    return DeployVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Clone a virtual folder.",
    )
)
async def clone_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: CloneVFolderInputGQL,
) -> CloneVFolderPayloadGQL | None:
    payload = await info.context.adapters.vfolder.clone(vfolder_id, input.to_pydantic())
    return CloneVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="List files in a virtual folder.",
    )
)
async def vfolder_list_files_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: ListFilesInputGQL,
) -> ListFilesPayloadGQL | None:
    payload = await info.context.adapters.vfolder.list_files(vfolder_id, input.to_pydantic())
    return ListFilesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create directories inside a virtual folder.",
    )
)
async def vfolder_mkdir_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: MkdirInputGQL,
) -> MkdirPayloadGQL | None:
    payload = await info.context.adapters.vfolder.mkdir(vfolder_id, input.to_pydantic())
    return MkdirPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Move a file within a virtual folder.",
    )
)
async def vfolder_move_file_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: MoveFileInputGQL,
) -> MoveFilePayloadGQL | None:
    payload = await info.context.adapters.vfolder.move_file(vfolder_id, input.to_pydantic())
    return MoveFilePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete files inside a virtual folder.",
    )
)
async def vfolder_delete_files_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: DeleteFilesInputGQL,
) -> DeleteFilesPayloadGQL | None:
    payload = await info.context.adapters.vfolder.delete_files(vfolder_id, input.to_pydantic())
    return DeleteFilesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create an upload session for a virtual folder.",
    )
)
async def vfolder_create_upload_session_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: UploadSessionInputGQL,
) -> UploadSessionPayloadGQL | None:
    payload = await info.context.adapters.vfolder.create_upload_session(
        vfolder_id, input.to_pydantic()
    )
    return UploadSessionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a download session for a virtual folder.",
    )
)
async def vfolder_create_download_session_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: DownloadSessionInputGQL,
) -> DownloadSessionPayloadGQL | None:
    payload = await info.context.adapters.vfolder.create_download_session(
        vfolder_id, input.to_pydantic()
    )
    return DownloadSessionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Soft-delete multiple virtual folders.",
    )
)
async def bulk_delete_vfolders_v2(
    info: Info[StrawberryGQLContext],
    input: BulkDeleteVFoldersInputGQL,
) -> BulkDeleteVFoldersPayloadGQL | None:
    """Soft-delete multiple virtual folders.

    Args:
        info: Strawberry GraphQL context.
        input: Input containing list of VFolder UUIDs to delete.

    Returns:
        BulkDeleteVFoldersPayloadGQL with count of deleted vfolders.
    """
    ctx = info.context
    dto = input.to_pydantic()
    payload = await ctx.adapters.vfolder.bulk_delete(dto)
    return BulkDeleteVFoldersPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description=(
            "Create a virtual folder owned by the specified project. "
            "Requires project-scoped CREATE permission."
        ),
    ),
    name="createVFolderInProject",
)
async def create_vfolder_in_project(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    input: CreateVFolderInScopeInputGQL,
) -> CreateVFolderPayloadGQL | None:
    """Create a new virtual folder scoped to a project."""
    payload = await info.context.adapters.vfolder.create_in_project(project_id, input.to_pydantic())
    return CreateVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Permanently purge multiple virtual folders.",
    )
)
async def bulk_purge_vfolders_v2(
    info: Info[StrawberryGQLContext],
    input: BulkPurgeVFoldersInputGQL,
) -> BulkPurgeVFoldersPayloadGQL | None:
    """Permanently purge multiple virtual folders, optionally cascading linked model cards."""
    ctx = info.context
    dto = input.to_pydantic()
    payload = await ctx.adapters.vfolder.bulk_purge(dto)
    return BulkPurgeVFoldersPayloadGQL.from_pydantic(payload)
