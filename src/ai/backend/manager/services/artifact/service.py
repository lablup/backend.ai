from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
    ImportArtifactActionResult,
)
from ai.backend.manager.services.artifact.actions.scan import (
    ScanArtifactsAction,
    ScanArtifactsActionResult,
)


class ArtifactService:
    _artifact_repository: ArtifactRepository
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._storage_manager = storage_manager

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        raise NotImplementedError

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        raise NotImplementedError
