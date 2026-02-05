from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, UNSET, Info

from ai.backend.manager.data.artifact_storages.types import ArtifactStorageUpdaterSpec
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_storage.actions.update import (
    UpdateArtifactStorageAction,
)
from ai.backend.manager.types import OptionalState

from .types import StrawberryGQLContext


@strawberry.input(description="Added in 25.16.0. Input for updating artifact storage metadata")
class UpdateArtifactStorageInput:
    """Input for updating artifact storage metadata (common fields like name)."""

    id: ID  # This is the storage_id (ObjectStorage.id or VFSStorage.id)
    name: str | None = UNSET

    def to_updater(self) -> Updater[ArtifactStorageRow]:
        spec = ArtifactStorageUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
        )
        return Updater(spec=spec, pk_value=uuid.UUID(self.id))


@strawberry.type(description="Added in 25.16.0. Payload for updating artifact storage metadata")
class UpdateArtifactStoragePayload:
    id: ID
    name: str


@strawberry.mutation(  # type: ignore[misc]
    name="updateArtifactStorage",
    description="Added in 25.16.0. Update artifact storage metadata (common fields like name)",
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
        id=ID(str(action_result.result.id)),
        name=action_result.result.name,
    )
