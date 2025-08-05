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

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
    ) -> None:
        self._artifact_repository = artifact_repository

    async def scan(self, action: ScanArtifactsAction) -> ScanArtifactsActionResult:
        raise NotImplementedError

    async def import_(self, action: ImportArtifactAction) -> ImportArtifactActionResult:
        raise NotImplementedError
