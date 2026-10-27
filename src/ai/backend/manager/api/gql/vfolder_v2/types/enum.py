"""VFolder GraphQL enum types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_enum


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
        description=(
            "Mount permission level for a virtual folder. "
            "NONE (added in 26.9.0) mounts to nobody; RW_DELETE mounts as READ_WRITE."
        ),
    ),
    name="VFolderMountPermission",
)
class VFolderMountPermissionGQL(StrEnum):
    NONE = "none"
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Ownership type of a virtual folder (USER or GROUP).",
    ),
    name="VFolderOwnershipType",
)
class VFolderOwnershipTypeGQL(StrEnum):
    USER = "user"
    GROUP = "group"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description=(
            "Operation status of a virtual folder. "
            f"CREATING (added in {NEXT_RELEASE_VERSION}) is set while the storage folder is being created."
        ),
    ),
    name="VFolderOperationStatus",
)
class VFolderOperationStatusGQL(StrEnum):
    READY = "ready"
    CREATING = "creating"
    CLONING = "cloning"
    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"
