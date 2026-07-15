"""GQL input and payload types for VFolder v2 mutations."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.vfolder.request import (
    BulkDeleteVFoldersInput as BulkDeleteInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    BulkPurgeVFoldersInput as BulkPurgeInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CloneVFolderInput as CloneInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateDownloadSessionInput as DownloadInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateUploadSessionInput as UploadInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInput as CreateInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateVFolderInScopeInput as CreateInScopeInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    DeleteFilesInput as DeleteFilesInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    DeployVFolderInput as DeployInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    ListFilesInput as ListFilesInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    MkdirInput as MkdirInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    MoveFileInput as MoveFileInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    PurgeVFolderOptions as PurgeVFolderOptionsDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkDeleteVFoldersPayload as BulkDeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkPurgeVFoldersPayload as BulkPurgePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkPurgeVFolderV2Error as BulkPurgeErrorDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CloneVFolderPayload as ClonePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateDownloadSessionPayload as DownloadPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateUploadSessionPayload as UploadPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateVFolderPayload as CreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    DeleteFilesPayload as DeleteFilesPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    DeleteVFolderPayload as DeletePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    DeployVFolderPayload as DeployPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    FileEntryNode as FileEntryNodeDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    ListFilesPayload as ListFilesPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    MkdirPayload as MkdirPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    MoveFilePayload as MoveFilePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    PurgeVFolderPayload as PurgePayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    RestoreVFolderPayload as RestorePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    PresetDeploymentStrategyInputGQL,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin
from ai.backend.manager.api.gql.vfolder_v2.types.enum import (
    VFolderMountPermissionGQL,
    VFolderUsageModeGQL,
)
from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL

# ============================================================
# Input types
# ============================================================


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a new virtual folder.",
    ),
    name="CreateVFolderV2Input",
)
class CreateVFolderInputGQL(PydanticInputMixin[CreateInputDTO]):
    name: str = gql_field(description="VFolder name.")
    project_id: UUID | None = gql_field(
        default=None, description="Project ID for project-owned vfolder."
    )
    host: str | None = gql_field(default=None, description="Storage host for the vfolder.")
    usage_mode: str = gql_field(
        default="general", description="Usage mode of the vfolder (general, model, data)."
    )
    permission: str = gql_field(
        default="rw", description="Default permission of the vfolder (ro, rw, wd)."
    )
    cloneable: bool = gql_field(default=False, description="Whether the vfolder is cloneable.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description=(
            "Scope-agnostic body for vfolder creation. The owning scope is "
            "supplied as a separate mutation argument."
        ),
    ),
    name="CreateVFolderInScopeInput",
)
class CreateVFolderInScopeInputGQL(PydanticInputMixin[CreateInScopeInputDTO]):
    name: str = gql_field(description="VFolder name.")
    host: str | None = gql_field(default=None, description="Storage host for the vfolder.")
    usage_mode: VFolderUsageModeGQL = gql_field(
        default=VFolderUsageModeGQL.GENERAL, description="Usage mode of the vfolder."
    )
    permission: VFolderMountPermissionGQL = gql_field(
        default=VFolderMountPermissionGQL.READ_WRITE,
        description="Default mount permission of the vfolder.",
    )
    cloneable: bool = gql_field(default=False, description="Whether the vfolder is cloneable.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for cloning a virtual folder.",
    ),
    name="CloneVFolderV2Input",
)
class CloneVFolderInputGQL(PydanticInputMixin[CloneInputDTO]):
    name: str = gql_field(description="Name for the cloned vfolder.")
    project_id: UUID | None = gql_field(
        default=None,
        description="Project ID for the cloned vfolder. If omitted, cloned as user-owned.",
    )
    host: str | None = gql_field(default=None, description="Target storage host for the clone.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for listing files in a virtual folder.",
    ),
    name="ListFilesV2Input",
)
class ListFilesInputGQL(PydanticInputMixin[ListFilesInputDTO]):
    path: str = gql_field(description="Directory path to list files from.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating directories inside a virtual folder.",
    ),
    name="MkdirV2Input",
)
class MkdirInputGQL(PydanticInputMixin[MkdirInputDTO]):
    path: list[str] = gql_field(description="Directory path(s) to create.")
    parents: bool = gql_field(default=True, description="Create parent directories if needed.")
    exist_ok: bool = gql_field(default=False, description="Do not raise error if directory exists.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for moving a file inside a virtual folder.",
    ),
    name="MoveFileV2Input",
)
class MoveFileInputGQL(PydanticInputMixin[MoveFileInputDTO]):
    src: str = gql_field(description="Source file path.")
    dst: str = gql_field(description="Destination file path.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for deleting files inside a virtual folder.",
    ),
    name="DeleteFilesV2Input",
)
class DeleteFilesInputGQL(PydanticInputMixin[DeleteFilesInputDTO]):
    files: list[str] = gql_field(description="List of file paths to delete.")
    recursive: bool = gql_field(
        default=False, description="Whether to delete directories recursively."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a file upload session.",
    ),
    name="CreateUploadSessionV2Input",
)
class UploadSessionInputGQL(PydanticInputMixin[UploadInputDTO]):
    path: str = gql_field(description="File path to upload to.")
    size: int = gql_field(description="File size in bytes.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a file download session.",
    ),
    name="CreateDownloadSessionV2Input",
)
class DownloadSessionInputGQL(PydanticInputMixin[DownloadInputDTO]):
    path: str = gql_field(description="File path to download.")
    archive: bool = gql_field(
        default=False, description="Whether to archive the file for download."
    )


# ============================================================
# Nested output types for payloads
# ============================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="A file or directory entry inside a virtual folder.",
    ),
    model=FileEntryNodeDTO,
    name="VFolderFileEntryV2",
)
class FileEntryNodeGQL(PydanticOutputMixin[FileEntryNodeDTO]):
    name: str = gql_field(description="File or directory name.")
    type: str = gql_field(description="Entry type (FILE, DIRECTORY, SYMLINK).")
    size: int = gql_field(description="File size in bytes.")
    mode: int = gql_field(description="POSIX file permission mode.")
    created_at: str = gql_field(description="Creation timestamp.")
    updated_at: str = gql_field(description="Last modification timestamp.")


# ============================================================
# Payload types
# ============================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after creating a virtual folder.",
    ),
    model=CreatePayloadDTO,
    name="CreateVFolderV2Payload",
)
class CreateVFolderPayloadGQL(PydanticOutputMixin[CreatePayloadDTO]):
    vfolder: VFolderGQL = gql_field(description="The created virtual folder.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after soft-deleting a virtual folder.",
    ),
    model=DeletePayloadDTO,
    name="DeleteVFolderV2Payload",
)
class DeleteVFolderPayloadGQL(PydanticOutputMixin[DeletePayloadDTO]):
    id: UUID = gql_field(description="ID of the deleted virtual folder.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after permanently purging a virtual folder.",
    ),
    model=PurgePayloadDTO,
    name="PurgeVFolderV2Payload",
)
class PurgeVFolderPayloadGQL(PydanticOutputMixin[PurgePayloadDTO]):
    id: UUID = gql_field(description="ID of the purged virtual folder.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after restoring a virtual folder from trash.",
    ),
    model=RestorePayloadDTO,
    name="RestoreVFolderPayload",
)
class RestoreVFolderPayloadGQL(PydanticOutputMixin[RestorePayloadDTO]):
    id: UUID = gql_field(description="ID of the restored virtual folder.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after cloning a virtual folder.",
    ),
    model=ClonePayloadDTO,
    name="CloneVFolderV2Payload",
)
class CloneVFolderPayloadGQL(PydanticOutputMixin[ClonePayloadDTO]):
    vfolder: VFolderGQL = gql_field(description="The cloned virtual folder.")
    bgtask_id: str = gql_field(description="Background task ID for the clone operation.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after listing files in a virtual folder.",
    ),
    model=ListFilesPayloadDTO,
    name="ListFilesV2Payload",
)
class ListFilesPayloadGQL(PydanticOutputMixin[ListFilesPayloadDTO]):
    items: list[FileEntryNodeGQL] = gql_field(description="List of file entries.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after creating directories in a virtual folder.",
    ),
    model=MkdirPayloadDTO,
    name="MkdirV2Payload",
)
class MkdirPayloadGQL(PydanticOutputMixin[MkdirPayloadDTO]):
    results: list[str] = gql_field(description="List of created directory paths.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after moving a file in a virtual folder.",
    ),
    model=MoveFilePayloadDTO,
    name="MoveFileV2Payload",
)
class MoveFilePayloadGQL(PydanticOutputMixin[MoveFilePayloadDTO]):
    src: str = gql_field(description="Source path that was moved.")
    dst: str = gql_field(description="Destination path.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after deleting files in a virtual folder.",
    ),
    model=DeleteFilesPayloadDTO,
    name="DeleteFilesV2Payload",
)
class DeleteFilesPayloadGQL(PydanticOutputMixin[DeleteFilesPayloadDTO]):
    bgtask_id: str = gql_field(description="Background task ID for the deletion operation.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after creating an upload session.",
    ),
    model=UploadPayloadDTO,
    name="CreateUploadSessionV2Payload",
)
class UploadSessionPayloadGQL(PydanticOutputMixin[UploadPayloadDTO]):
    token: str = gql_field(description="Upload session token.")
    url: str = gql_field(description="Upload URL.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload returned after creating a download session.",
    ),
    model=DownloadPayloadDTO,
    name="CreateDownloadSessionV2Payload",
)
class DownloadSessionPayloadGQL(PydanticOutputMixin[DownloadPayloadDTO]):
    token: str = gql_field(description="Download session token.")
    url: str = gql_field(description="Download URL.")


# ============================================================
# Bulk operation types
# ============================================================


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for soft-deleting multiple virtual folders.",
    ),
    name="BulkDeleteVFoldersV2Input",
)
class BulkDeleteVFoldersInputGQL(PydanticInputMixin[BulkDeleteInputDTO]):
    ids: list[UUID] = gql_field(description="List of VFolder UUIDs to soft-delete.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for bulk virtual folder soft-deletion.",
    ),
    model=BulkDeletePayloadDTO,
    name="BulkDeleteVFoldersV2Payload",
)
class BulkDeleteVFoldersPayloadGQL(PydanticOutputMixin[BulkDeletePayloadDTO]):
    deleted_count: int = gql_field(
        description="Number of virtual folders successfully soft-deleted."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Optional behavior flags for vfolder purge operations.",
    ),
    name="PurgeVFolderOptionsInput",
)
class PurgeVFolderOptionsInputGQL(PydanticInputMixin[PurgeVFolderOptionsDTO]):
    cascade_model_card: bool = gql_field(
        default=False,
        description=(
            "If true, also delete model card record(s) referencing the vfolder. "
            "If false, the request is rejected when any model card still references it."
        ),
    )
    force: bool = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "If true, bypass the in-use guards and purge the vfolder even when it is "
                "mounted by a live session, referenced by an active model-service endpoint, "
                "or not in a purgable status. Irreversible — use with caution. "
                "If false (default), the request is rejected in those cases."
            ),
        ),
        default=False,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for permanently purging multiple virtual folders.",
    ),
    name="BulkPurgeVFoldersV2Input",
)
class BulkPurgeVFoldersInputGQL(PydanticInputMixin[BulkPurgeInputDTO]):
    ids: list[UUID] = gql_field(description="List of VFolder UUIDs to purge.")
    options: PurgeVFolderOptionsInputGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description=(
                "Optional behavior flags applied to every vfolder in the batch. "
                "Defaults to all-false when omitted."
            ),
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Failure detail for a single vfolder in a bulk purge.",
    ),
    model=BulkPurgeErrorDTO,
    name="BulkPurgeVFolderV2Error",
)
class BulkPurgeVFolderV2ErrorGQL(PydanticOutputMixin[BulkPurgeErrorDTO]):
    vfolder_id: UUID = gql_field(description="UUID of the vfolder that failed to purge.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for bulk virtual folder purge.",
    ),
    model=BulkPurgePayloadDTO,
    name="BulkPurgeVFoldersV2Payload",
)
class BulkPurgeVFoldersPayloadGQL(PydanticOutputMixin[BulkPurgePayloadDTO]):
    purged_count: int = gql_field(description="Number of virtual folders successfully purged.")
    failed: list[BulkPurgeVFolderV2ErrorGQL] = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="List of errors for vfolders that failed to purge.",
        ),
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for deploying a model VFolder as a new deployment.",
    ),
    name="DeployVFolderV2Input",
)
class DeployVFolderInputGQL(PydanticInputMixin[DeployInputDTO]):
    project_id: UUID = gql_field(description="Target project UUID for the deployment.")
    revision_preset_id: UUID = gql_field(description="Deployment revision preset UUID.")
    resource_group: str = gql_field(description="Resource group name.")
    desired_replica_count: int = gql_field(default=1, description="Number of replicas.")
    open_to_public: bool | None = gql_field(
        default=None,
        description="Override open_to_public. Defaults to the preset value, then False.",
    )
    replica_count: int | None = gql_field(
        default=None,
        description="Override replica_count. Defaults to the preset value, then desired_replica_count.",
    )
    revision_history_limit: int | None = gql_field(
        default=None,
        description="Override revision_history_limit. Defaults to the preset value, then 10.",
    )
    deployment_strategy: PresetDeploymentStrategyInputGQL | None = gql_field(
        default=None,
        description="Override deployment strategy. Defaults to the preset value, then none.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for deploying a model VFolder.",
    ),
    model=DeployPayloadDTO,
    name="DeployVFolderV2Payload",
)
class DeployVFolderPayloadGQL(PydanticOutputMixin[DeployPayloadDTO]):
    deployment_id: UUID = gql_field(description="ID of the created deployment.")
    deployment_name: str = gql_field(description="Name of the created deployment.")
