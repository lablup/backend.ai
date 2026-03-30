"""VFolder GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderAccessControlInfo as VFolderAccessControlInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderMetadataInfo as VFolderMetadataInfoDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.vfolder_v2.types.enum import (
    VFolderMountPermissionGQL,
    VFolderOwnershipTypeGQL,
    VFolderUsageModeGQL,
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Descriptive metadata for a virtual folder. "
            "Includes the folder name, usage mode, quota scope, "
            "timestamps, and clone eligibility."
        ),
    ),
    model=VFolderMetadataInfoDTO,
    name="VFolderMetadataInfo",
)
class VFolderMetadataInfoGQL:
    """Descriptive metadata fields for a virtual folder."""

    name: str = gql_field(description="Display name of the virtual folder.")
    usage_mode: VFolderUsageModeGQL = gql_field(
        description="Usage mode: GENERAL (normal), MODEL (shared models), or DATA (shared datasets)."
    )
    quota_scope_id: str | None = gql_field(
        description="Quota scope identifier that governs storage limits for this folder."
    )
    created_at: datetime = gql_field(description="Timestamp when the virtual folder was created.")
    last_used: datetime | None = gql_field(
        description="Timestamp of the most recent access. Null if never accessed after creation."
    )
    cloneable: bool = gql_field(
        description="Whether this virtual folder can be cloned by other users."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Access control information for a virtual folder. "
            "Includes the mount permission level (read-only, read-write, read-write-delete) "
            "and ownership type (user or project)."
        ),
    ),
    model=VFolderAccessControlInfoDTO,
    name="VFolderAccessControlInfo",
)
class VFolderAccessControlInfoGQL:
    """Access control and ownership type information."""

    permission: VFolderMountPermissionGQL = gql_field(
        description="Mount permission level: READ_ONLY (ro), READ_WRITE (rw), or RW_DELETE (wd)."
    )
    ownership_type: VFolderOwnershipTypeGQL = gql_field(
        description="Ownership type: USER (personal folder) or GROUP (project-shared folder)."
    )
