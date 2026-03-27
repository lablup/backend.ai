"""VFolderV2 GraphQL enum types."""

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
    name="VFolderPermissionField",
)
class VFolderPermissionGQL(StrEnum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Ownership type of a virtual folder (USER or GROUP).",
    ),
    name="VFolderOwnershipTypeField",
)
class VFolderOwnershipTypeGQL(StrEnum):
    USER = "user"
    GROUP = "group"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Operation status of a virtual folder.",
    ),
    name="VFolderOperationStatusField",
)
class VFolderOperationStatusGQL(StrEnum):
    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"
    DELETE_PENDING = "delete-pending"
    DELETE_ONGOING = "delete-ongoing"
    DELETE_COMPLETE = "delete-complete"
    DELETE_ERROR = "delete-error"
