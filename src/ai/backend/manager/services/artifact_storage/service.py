import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.artifact_storage.repository import ArtifactStorageRepository
from ai.backend.manager.services.artifact_storage.actions.update import (
    UpdateArtifactStorageAction,
    UpdateArtifactStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactStorageService:
    """Service layer for artifact storage operations."""

    _artifact_storage_repository: ArtifactStorageRepository

    def __init__(
        self,
        artifact_storage_repository: ArtifactStorageRepository,
    ) -> None:
        self._artifact_storage_repository = artifact_storage_repository

    async def update(
        self, action: UpdateArtifactStorageAction
    ) -> UpdateArtifactStorageActionResult:
        """
        Update an existing artifact storage.
        """
        log.info("Updating artifact storage with id: {}", action.updater.pk_value)
        storage_data = await self._artifact_storage_repository.update(action.updater)
        return UpdateArtifactStorageActionResult(result=storage_data)
