import logging

from ai.backend.common.events.event_types.artifact.anycast import (
    ModelImportDoneEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import ArtifactStatus
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactEventHandler:
    _artifact_repository: ArtifactRepository
    _huggingface_repository: HuggingFaceRepository

    def __init__(
        self, artifact_repository: ArtifactRepository, huggingface_repository: HuggingFaceRepository
    ) -> None:
        self._artifact_repository = artifact_repository
        self._huggingface_repository = huggingface_repository

    async def handle_artifact_import_done(
        self,
        context: None,
        source: AgentId,
        event: ModelImportDoneEvent,
    ) -> None:
        model_id = event.model_id
        artifact_total_size = event.total_size

        registry_data = await self._huggingface_repository.get_registry_data_by_name(
            event.registry_name
        )

        artifact = await self._artifact_repository.get_model_artifact(
            model_id, registry_id=registry_data.id
        )

        revision = await self._artifact_repository.get_artifact_revision(
            artifact.id, revision=event.revision
        )

        await self._artifact_repository.update_artifact_revision_bytesize(
            revision.id, artifact_total_size
        )

        await self._artifact_repository.update_artifact_revision_bytesize(
            revision.id, artifact_total_size
        )
        await self._artifact_repository.update_artifact_revision_status(
            revision.id, ArtifactStatus.PULLED
        )
        # TODO: Add verify step
        await self._artifact_repository.update_artifact_revision_status(
            revision.id, ArtifactStatus.VERIFYING
        )
        await self._artifact_repository.update_artifact_revision_status(
            revision.id, ArtifactStatus.NEEDS_APPROVAL
        )
