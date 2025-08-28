import logging

from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanArtifactRegistryEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryEventHandler:
    _artifact_repository: ArtifactRepository
    _huggingface_repository: HuggingFaceRepository

    def __init__(
        self, artifact_repository: ArtifactRepository, huggingface_repository: HuggingFaceRepository
    ) -> None:
        self._artifact_repository = artifact_repository
        self._huggingface_repository = huggingface_repository

    async def handle_artifact_registry_scan(
        self, context: None, source: AgentId, event: DoScanArtifactRegistryEvent
    ) -> None:
        print("Handling artifact registry scan event")
        pass
