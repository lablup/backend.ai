"""VFolder GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
    CreateVFolderPayloadGQL,
    DeleteFilesInputGQL,
    DeleteFilesPayloadGQL,
    DeleteVFolderPayloadGQL,
    DownloadSessionInputGQL,
    DownloadSessionPayloadGQL,
    ListFilesInputGQL,
    ListFilesPayloadGQL,
    MkdirInputGQL,
    MkdirPayloadGQL,
    MoveFileInputGQL,
    MoveFilePayloadGQL,
    PurgeVFolderPayloadGQL,
    UploadSessionInputGQL,
    UploadSessionPayloadGQL,
)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new virtual folder.",
    )
)  # type: ignore[misc]
async def create_vfolder_v2(
    info: Info[StrawberryGQLContext],
    input: CreateVFolderInputGQL,
) -> CreateVFolderPayloadGQL:
    payload = await info.context.adapters.vfolder.create(input.to_pydantic())
    return CreateVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete a virtual folder (move to trash).",
    )
)  # type: ignore[misc]
async def delete_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
) -> DeleteVFolderPayloadGQL:
    payload = await info.context.adapters.vfolder.delete(vfolder_id)
    return DeleteVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently purge a virtual folder.",
    )
)  # type: ignore[misc]
async def purge_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
) -> PurgeVFolderPayloadGQL:
    payload = await info.context.adapters.vfolder.purge(vfolder_id)
    return PurgeVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Clone a virtual folder.",
    )
)  # type: ignore[misc]
async def clone_vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: CloneVFolderInputGQL,
) -> CloneVFolderPayloadGQL:
    payload = await info.context.adapters.vfolder.clone(vfolder_id, input.to_pydantic())
    return CloneVFolderPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List files in a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_list_files_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: ListFilesInputGQL,
) -> ListFilesPayloadGQL:
    payload = await info.context.adapters.vfolder.list_files(vfolder_id, input.to_pydantic())
    return ListFilesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create directories inside a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_mkdir_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: MkdirInputGQL,
) -> MkdirPayloadGQL:
    payload = await info.context.adapters.vfolder.mkdir(vfolder_id, input.to_pydantic())
    return MkdirPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Move a file within a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_move_file_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: MoveFileInputGQL,
) -> MoveFilePayloadGQL:
    payload = await info.context.adapters.vfolder.move_file(vfolder_id, input.to_pydantic())
    return MoveFilePayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete files inside a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_delete_files_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: DeleteFilesInputGQL,
) -> DeleteFilesPayloadGQL:
    payload = await info.context.adapters.vfolder.delete_files(vfolder_id, input.to_pydantic())
    return DeleteFilesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create an upload session for a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_create_upload_session_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: UploadSessionInputGQL,
) -> UploadSessionPayloadGQL:
    payload = await info.context.adapters.vfolder.create_upload_session(
        vfolder_id, input.to_pydantic()
    )
    return UploadSessionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a download session for a virtual folder.",
    )
)  # type: ignore[misc]
async def vfolder_create_download_session_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
    input: DownloadSessionInputGQL,
) -> DownloadSessionPayloadGQL:
    payload = await info.context.adapters.vfolder.create_download_session(
        vfolder_id, input.to_pydantic()
    )
    return DownloadSessionPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete multiple virtual folders.",
    )
)  # type: ignore[misc]
async def bulk_delete_vfolders_v2(
    info: Info[StrawberryGQLContext],
    input: BulkDeleteVFoldersInputGQL,
) -> BulkDeleteVFoldersPayloadGQL:
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
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently purge multiple virtual folders.",
    )
)  # type: ignore[misc]
async def bulk_purge_vfolders_v2(
    info: Info[StrawberryGQLContext],
    input: BulkPurgeVFoldersInputGQL,
) -> BulkPurgeVFoldersPayloadGQL:
    """Permanently purge multiple virtual folders.

    Args:
        info: Strawberry GraphQL context.
        input: Input containing list of VFolder UUIDs to purge.

    Returns:
        BulkPurgeVFoldersPayloadGQL with count of purged vfolders.
    """
    ctx = info.context
    dto = input.to_pydantic()
    payload = await ctx.adapters.vfolder.bulk_purge(dto)
    return BulkPurgeVFoldersPayloadGQL.from_pydantic(payload)
