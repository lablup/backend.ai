import logging

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.events.event_types.artifact.anycast import (
    ModelImportDoneEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactEventHandler:
    _artifact_repository: ArtifactRepository

    def __init__(self, artifact_repository: ArtifactRepository) -> None:
        self._artifact_repository = artifact_repository

    async def handle_artifact_import_done(
        self,
        context: None,
        source: AgentId,
        event: ModelImportDoneEvent,
    ) -> None:
        model_id = event.model_id
        revision = event.revision
        artifact_total_size = event.total_size

        artifact = await self._artifact_repository.get_artifact_by_model_target(
            ModelTarget(model_id=model_id, revision=revision)
        )

        await self._artifact_repository.update_artifact_bytesize(artifact.id, artifact_total_size)
