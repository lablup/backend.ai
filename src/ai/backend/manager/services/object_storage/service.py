import logging
from pathlib import Path

from ai.backend.common.dto.storage.request import (
    PresignedDownloadObjectReq,
    PresignedUploadObjectReq,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import ArtifactStatus
from ai.backend.manager.errors.artifact import ArtifactNotApproved, ArtifactReadonly
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.object_storage import ObjectStorageOperationNotSupported
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
    CreateObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.delete import (
    DeleteObjectStorageAction,
    DeleteObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.get import (
    GetObjectStorageAction,
    GetObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
    GetDownloadPresignedURLActionResult,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
    GetUploadPresignedURLActionResult,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
    ListObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.search import (
    SearchObjectStoragesAction,
    SearchObjectStoragesActionResult,
)
from ai.backend.manager.services.object_storage.actions.update import (
    UpdateObjectStorageAction,
    UpdateObjectStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ObjectStorageService:
    _artifact_repository: ArtifactRepository
    _object_storage_repository: ObjectStorageRepository
    _storage_namespace_repository: StorageNamespaceRepository
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        object_storage_repository: ObjectStorageRepository,
        storage_namespace_repository: StorageNamespaceRepository,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._object_storage_repository = object_storage_repository
        self._storage_namespace_repository = storage_namespace_repository
        self._storage_manager = storage_manager
        self._config_provider = config_provider

    async def create(self, action: CreateObjectStorageAction) -> CreateObjectStorageActionResult:
        """
        Create a new object storage.
        """
        log.info("Creating object storage with data: {}", action.creator)
        storage_data = await self._object_storage_repository.create(action.creator)
        return CreateObjectStorageActionResult(result=storage_data)

    async def update(self, action: UpdateObjectStorageAction) -> UpdateObjectStorageActionResult:
        """
        Update an existing object storage.
        """
        log.info("Updating object storage with id: {}", action.updater.pk_value)
        storage_data = await self._object_storage_repository.update(action.updater)
        return UpdateObjectStorageActionResult(result=storage_data)

    async def delete(self, action: DeleteObjectStorageAction) -> DeleteObjectStorageActionResult:
        """
        Delete an existing object storage.
        """
        log.info("Deleting object storage with id: {}", action.storage_id)
        storage_data = await self._object_storage_repository.delete(action.storage_id)
        return DeleteObjectStorageActionResult(deleted_storage_id=storage_data)

    async def get(self, action: GetObjectStorageAction) -> GetObjectStorageActionResult:
        """
        Get an existing object storage by ID.
        """
        log.info("Getting object storage with id: {}", action.storage_id)
        storage_data = await self._object_storage_repository.get_by_id(action.storage_id)
        return GetObjectStorageActionResult(result=storage_data)

    # TODO: Add filtering logic
    async def list(self, action: ListObjectStorageAction) -> ListObjectStorageActionResult:
        """
        List all object storages.
        """
        log.info("Listing object storages")
        storage_data_list = await self._object_storage_repository.list_object_storages()
        return ListObjectStorageActionResult(data=storage_data_list)

    async def search(self, action: SearchObjectStoragesAction) -> SearchObjectStoragesActionResult:
        """Searches Object storages."""
        result = await self._object_storage_repository.search(
            querier=action.querier,
        )
        return SearchObjectStoragesActionResult(
            storages=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_presigned_download_url(
        self, action: GetDownloadPresignedURLAction
    ) -> GetDownloadPresignedURLActionResult:
        """
        Get a presigned download URL for an existing object storage.
        """
        log.info(
            "Getting presigned download URL for object storage, artifact_revision: {}",
            action.artifact_revision_id,
        )

        reservoir_config = self._config_provider.config.reservoir
        if reservoir_config is None:
            raise ServerMisconfiguredError("Reservoir configuration is missing")

        storage_name = reservoir_config.archive_storage

        # Only object storage is supported for presigned URLs
        if reservoir_config.config.storage_type != "object_storage":
            raise ObjectStorageOperationNotSupported(
                "Presigned URLs are only supported for object storage"
            )

        bucket_name = reservoir_config.config.bucket_name
        storage_data = await self._object_storage_repository.get_by_name(storage_name)
        storage_namespace = await self._storage_namespace_repository.get_by_storage_and_namespace(
            storage_data.id, bucket_name
        )
        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        artifact_data = await self._artifact_repository.get_artifact_by_id(
            revision_data.artifact_id
        )

        if revision_data.status != ArtifactStatus.AVAILABLE:
            raise ArtifactNotApproved("Only available artifacts can be downloaded.")

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        # Build S3 key
        object_path = Path(artifact_data.name) / revision_data.version / action.key

        result = await storage_proxy_client.get_s3_presigned_download_url(
            storage_data.name,
            storage_namespace.namespace,
            PresignedDownloadObjectReq(key=str(object_path), expiration=action.expiration),
        )

        return GetDownloadPresignedURLActionResult(
            storage_id=storage_data.id, presigned_url=result.url
        )

    async def get_presigned_upload_url(
        self, action: GetUploadPresignedURLAction
    ) -> GetUploadPresignedURLActionResult:
        """
        Get a presigned upload URL for an existing object storage.
        """
        log.info(
            "Getting presigned upload URL for object storage with artifact id: {}",
            action.artifact_revision_id,
        )

        reservoir_config = self._config_provider.config.reservoir
        if reservoir_config is None:
            raise ServerMisconfiguredError("Reservoir configuration is missing")

        storage_name = reservoir_config.archive_storage

        # Only object storage is supported for presigned URLs
        if reservoir_config.config.storage_type != "object_storage":
            raise ObjectStorageOperationNotSupported(
                "Presigned URLs are only supported for object storage"
            )

        bucket_name = reservoir_config.config.bucket_name
        storage_data = await self._object_storage_repository.get_by_name(storage_name)
        storage_namespace = await self._storage_namespace_repository.get_by_storage_and_namespace(
            storage_data.id, bucket_name
        )

        revision_data = await self._artifact_repository.get_artifact_revision_by_id(
            action.artifact_revision_id
        )
        artifact_data = await self._artifact_repository.get_artifact_by_id(
            revision_data.artifact_id
        )

        if artifact_data.readonly:
            raise ArtifactReadonly("Cannot upload to a readonly artifact.")

        storage_proxy_client = self._storage_manager.get_manager_facing_client(storage_data.host)

        # Build S3 key
        object_path = Path(artifact_data.name) / revision_data.version / action.key

        result = await storage_proxy_client.get_s3_presigned_upload_url(
            storage_data.name,
            storage_namespace.namespace,
            PresignedUploadObjectReq(
                key=str(object_path),
            ),
        )

        return GetUploadPresignedURLActionResult(
            storage_id=storage_data.id, presigned_url=result.url, fields=result.fields
        )
