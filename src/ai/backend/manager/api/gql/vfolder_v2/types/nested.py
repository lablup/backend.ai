"""VFolder GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderAccessControlInfo as VFolderAccessControlInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderMetadataInfo as VFolderMetadataInfoDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderOwnershipInfo as VFolderOwnershipInfoDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_v2.types.enum import (
    VFolderMountPermissionGQL,
    VFolderOwnershipTypeGQL,
    VFolderUsageModeGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Ownership context for a virtual folder. "
            "Provides both scalar IDs (userId, projectId, creatorEmail) for lightweight access "
            "and full node resolvers (user, project, creator) for detailed entity information."
        ),
    ),
    model=VFolderOwnershipInfoDTO,
    name="VFolderOwnershipInfo",
)
class VFolderOwnershipInfoGQL:
    """Ownership context with scalar IDs and node resolvers."""

    user_id: UUID | None = gql_field(
        description="UUID of the user who owns this virtual folder. Null for project-owned folders.",
    )
    project_id: UUID | None = gql_field(
        description="UUID of the project that owns this virtual folder. Null for user-owned folders.",
    )
    creator_id: UUID | None = gql_field(
        description="UUID of the user who originally created this virtual folder.",
    )
    creator_email: str | None = gql_field(
        description="Email of the user who originally created this virtual folder.",
    )

    @gql_field(description="The user who owns this virtual folder. Null for project-owned folders.")  # type: ignore[misc]
    async def user(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        if self.user_id is None:
            return None
        return await info.context.data_loaders.user_loader.load(self.user_id)

    @gql_field(
        description="The project that owns this virtual folder. Null for user-owned folders."
    )  # type: ignore[misc]
    async def project(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ProjectV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
        ]
        | None
    ):
        if self.project_id is None:
            return None
        return await info.context.data_loaders.project_loader.load(self.project_id)

    @gql_field(description="The user who originally created this virtual folder.")  # type: ignore[misc]
    async def creator(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        if self.creator_id is None:
            return None
        return await info.context.data_loaders.user_loader.load(self.creator_id)
