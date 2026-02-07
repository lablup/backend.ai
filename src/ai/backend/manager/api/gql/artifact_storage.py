from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Self

import strawberry
from strawberry import ID, UNSET, Info

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.data.artifact_storages.types import (
    ArtifactStorageData,
    ArtifactStorageUpdaterSpec,
)
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_storage.actions.update import (
    UpdateArtifactStorageAction,
)
from ai.backend.manager.types import OptionalState

from .types import StrawberryGQLContext


@strawberry.enum(
    name="ArtifactStorageType",
    description=(
        "Added in 26.2.0. The type of artifact storage backend. "
        "OBJECT_STORAGE: Object storage (e.g., S3-compatible). "
        "VFS_STORAGE: Virtual folder storage. "
        "GIT_LFS: Git LFS storage."
    ),
)
class ArtifactStorageTypeGQL(StrEnum):
    """Artifact storage type enum."""

    OBJECT_STORAGE = "object_storage"
    VFS_STORAGE = "vfs_storage"
    GIT_LFS = "git_lfs"

    @classmethod
    def from_internal(cls, internal_type: ArtifactStorageType) -> ArtifactStorageTypeGQL:
        """Convert internal ArtifactStorageType to GraphQL enum."""
        match internal_type:
            case ArtifactStorageType.OBJECT_STORAGE:
                return cls.OBJECT_STORAGE
            case ArtifactStorageType.VFS_STORAGE:
                return cls.VFS_STORAGE
            case ArtifactStorageType.GIT_LFS:
                return cls.GIT_LFS

    def to_internal(self) -> ArtifactStorageType:
        """Convert GraphQL enum to internal ArtifactStorageType."""
        match self:
            case ArtifactStorageTypeGQL.OBJECT_STORAGE:
                return ArtifactStorageType.OBJECT_STORAGE
            case ArtifactStorageTypeGQL.VFS_STORAGE:
                return ArtifactStorageType.VFS_STORAGE
            case ArtifactStorageTypeGQL.GIT_LFS:
                return ArtifactStorageType.GIT_LFS


@strawberry.type(description="Added in 26.2.0. Artifact storage metadata")
class ArtifactStorage:
    id: ID = strawberry.field(description="The ID of the artifact storage")
    name: str = strawberry.field(description="The name of the artifact storage")
    storage_id: ID = strawberry.field(
        description="The ID of the underlying storage (ObjectStorage or VFSStorage)"
    )
    type: ArtifactStorageTypeGQL = strawberry.field(description="The type of the artifact storage")

    @classmethod
    def from_dataclass(cls, data: ArtifactStorageData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            storage_id=ID(str(data.storage_id)),
            type=ArtifactStorageTypeGQL.from_internal(data.type),
        )


@strawberry.input(description="Added in 26.2.0. Input for updating artifact storage metadata")
class UpdateArtifactStorageInput:
    """Input for updating artifact storage metadata (common fields like name)."""

    id: ID = strawberry.field(description="The ID of the artifact storage")
    name: str | None = strawberry.field(
        default=UNSET, description="The new name for the artifact storage"
    )

    def to_updater(self) -> Updater[ArtifactStorageRow]:
        spec = ArtifactStorageUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
        )
        return Updater(spec=spec, pk_value=uuid.UUID(self.id))


@strawberry.type(description="Added in 26.2.0. Payload for updating artifact storage metadata")
class UpdateArtifactStoragePayload:
    artifact_storage: ArtifactStorage = strawberry.field(description="The updated artifact storage")


@strawberry.mutation(  # type: ignore[misc]
    name="updateArtifactStorage",
    description="Added in 26.2.0. Update artifact storage metadata (common fields like name)",
)
async def update_artifact_storage(
    input: UpdateArtifactStorageInput, info: Info[StrawberryGQLContext]
) -> UpdateArtifactStoragePayload:
    processors = info.context.processors

    action_result = await processors.artifact_storage.update.wait_for_complete(
        UpdateArtifactStorageAction(
            updater=input.to_updater(),
        )
    )

    return UpdateArtifactStoragePayload(
        artifact_storage=ArtifactStorage.from_dataclass(action_result.result),
    )
