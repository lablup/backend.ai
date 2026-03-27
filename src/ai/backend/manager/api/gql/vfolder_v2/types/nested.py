"""VFolderV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderBasicInfo as VFolderBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderOwnerInfo as VFolderOwnerInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderPermissionInfo as VFolderPermissionInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderUsageInfo as VFolderUsageInfoDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Core identity and status fields for a virtual folder. "
            "Includes the folder name, storage host location, quota scope, "
            "usage mode (general/model/data), current operation status, "
            "and timestamps."
        ),
    ),
    model=VFolderBasicInfoDTO,
    name="VFolderBasicInfo",
)
class VFolderBasicInfoGQL:
    """Core identity and status fields for a virtual folder."""

    id: UUID = gql_field(description="Unique identifier of the virtual folder (UUID).")
    name: str = gql_field(description="Display name of the virtual folder.")
    host: str = gql_field(
        description="Storage host where the virtual folder is physically located."
    )
    quota_scope_id: str | None = gql_field(
        description="Quota scope identifier that governs storage limits for this folder."
    )
    usage_mode: strawberry.auto = gql_field(
        description="Usage mode: GENERAL (normal), MODEL (shared models), or DATA (shared datasets)."
    )
    status: strawberry.auto = gql_field(
        description=(
            "Current operation status. "
            "READY, PERFORMING, CLONING, MOUNTED, ERROR, "
            "DELETE_PENDING, DELETE_ONGOING, DELETE_COMPLETE, or DELETE_ERROR."
        )
    )
    created_at: datetime = gql_field(description="Timestamp when the virtual folder was created.")
    last_used: datetime | None = gql_field(
        description="Timestamp of the most recent access. Null if never accessed after creation."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Access control information for a virtual folder. "
            "Includes the mount permission level (read-only, read-write, read-write-delete), "
            "ownership type (user or project), whether the querying user is the owner, "
            "and clone eligibility."
        ),
    ),
    model=VFolderPermissionInfoDTO,
    name="VFolderPermissionInfo",
)
class VFolderPermissionInfoGQL:
    """Access control and ownership type information."""

    permission: strawberry.auto = gql_field(
        description="Mount permission level: READ_ONLY (ro), READ_WRITE (rw), or RW_DELETE (wd)."
    )
    ownership_type: strawberry.auto = gql_field(
        description="Ownership type: USER (personal folder) or GROUP (project-shared folder)."
    )
    is_owner: bool = gql_field(
        description="Whether the current querying user is the owner of this virtual folder."
    )
    cloneable: bool = gql_field(
        description="Whether this virtual folder can be cloned by other users."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Owner context for a virtual folder. "
            "Identifies the user or project that owns this virtual folder "
            "and the account that originally created it."
        ),
    ),
    model=VFolderOwnerInfoDTO,
    name="VFolderOwnerInfo",
)
class VFolderOwnerInfoGQL:
    """Owner context identifying who owns and created this virtual folder."""

    user_id: UUID | None = gql_field(
        description="UUID of the owning user. Set when ownership_type is USER, null otherwise."
    )
    group_id: UUID | None = gql_field(
        description="UUID of the owning project/group. Set when ownership_type is GROUP, null otherwise."
    )
    creator: str | None = gql_field(
        description="Email address of the user who originally created this virtual folder."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Storage usage statistics for a virtual folder. "
            "Reports current file count and byte usage, along with "
            "configured quota limits. May be null in list responses "
            "where usage data is not loaded for performance reasons."
        ),
    ),
    model=VFolderUsageInfoDTO,
    name="VFolderUsageInfo",
)
class VFolderUsageInfoGQL:
    """Storage usage statistics and quota limits."""

    num_files: int = gql_field(description="Current number of files stored in the virtual folder.")
    used_bytes: int = gql_field(
        description="Total storage space used by the virtual folder, in bytes."
    )
    max_size: int | None = gql_field(
        description="Maximum allowed storage size in bytes. Null if unlimited."
    )
    max_files: int = gql_field(
        description="Maximum allowed number of files. 0 indicates no limit is configured."
    )
