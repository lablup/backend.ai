"""VFolder GraphQL enum types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_enum


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Usage mode of a virtual folder (GENERAL, MODEL, DATA).",
    ),
    name="VFolderUsageMode",
)
class VFolderUsageModeGQL(StrEnum):
    GENERAL = "general"
    MODEL = "model"
    DATA = "data"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Mount permission level for a virtual folder.",
    ),
    name="VFolderMountPermission",
)
class VFolderMountPermissionGQL(StrEnum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Ownership type of a virtual folder (USER or GROUP).",
    ),
    name="VFolderOwnershipType",
)
class VFolderOwnershipTypeGQL(StrEnum):
    USER = "user"
    GROUP = "group"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Operation status of a virtual folder.",
    ),
    name="VFolderOperationStatus",
)
class VFolderOperationStatusGQL(StrEnum):
    READY = "ready"
    CLONING = "cloning"
    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Host-level permission for virtual folder storage hosts. "
            "CREATE: Create new vfolders on the host. "
            "MODIFY: Rename or update vfolder options. "
            "DELETE: Delete vfolders from the host. "
            "MOUNT_IN_SESSION: Mount vfolders in compute sessions. "
            "UPLOAD_FILE: Upload files to vfolders. "
            "DOWNLOAD_FILE: Download files from vfolders. "
            "INVITE_OTHERS: Invite other users to user-type vfolders. "
            "SET_USER_PERM: Override permission of group-type vfolders."
        ),
    ),
    name="VFolderHostPermission",
)
class VFolderHostPermissionGQL(StrEnum):
    CREATE = "create-vfolder"
    MODIFY = "modify-vfolder"
    DELETE = "delete-vfolder"
    MOUNT_IN_SESSION = "mount-in-session"
    UPLOAD_FILE = "upload-file"
    DOWNLOAD_FILE = "download-file"
    INVITE_OTHERS = "invite-others"
    SET_USER_PERM = "set-user-specific-permission"
