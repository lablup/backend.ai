import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
    CreateObjectStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ObjectStorageService:
    _object_storage_repository: ObjectStorageRepository

    def __init__(self, object_storage_repository: ObjectStorageRepository) -> None:
        self._object_storage_repository = object_storage_repository

    async def create(self, action: CreateObjectStorageAction) -> CreateObjectStorageActionResult:
        """
        Create a new object storage.
        """
        log.info("Creating object storage with data: {}", action.creator)
        storage_data = await self._object_storage_repository.create(action.creator)
        return CreateObjectStorageActionResult(result=storage_data)
