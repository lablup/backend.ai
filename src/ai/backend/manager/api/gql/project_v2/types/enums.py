"""ProjectV2 GraphQL enum types."""

from __future__ import annotations

from enum import StrEnum

import strawberry


@strawberry.enum(
    name="ProjectTypeV2",
    description=(
        "Added in 26.2.0. Project type determining its purpose and behavior. "
        "GENERAL: Standard project for general computation. "
        "MODEL_STORE: Project for model storage and management."
    ),
)
class ProjectV2TypeEnum(StrEnum):
    """Project type enum."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


@strawberry.enum(
    name="VFolderHostPermissionV2",
    description=("Added in 26.2.0. Atomic permissions for virtual folders on a storage host."),
)
class VFolderHostPermissionEnum(StrEnum):
    """Virtual folder host permission enum."""

    CREATE_VFOLDER = "create-vfolder"
    MODIFY_VFOLDER = "modify-vfolder"
    DELETE_VFOLDER = "delete-vfolder"
    MOUNT_IN_SESSION = "mount-in-session"
    UPLOAD_FILE = "upload-file"
    DOWNLOAD_FILE = "download-file"
    INVITE_OTHERS = "invite-others"
    SET_USER_PERM = "set-user-specific-permission"
