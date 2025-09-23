import logging

from ai.backend.common.dto.storage.response import (
    ObjectMetaResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
)
from ai.backend.common.types import StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import (
    ObjectStorageBucketNotFoundError,
    StorageNotFoundError,
    StorageTypeInvalidError,
)
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ObjectStorageService:
    """
    Service class for S3 storage operations.
    """

    _storage_pool: StoragePool

    def __init__(self, storage_pool: StoragePool) -> None:
        self._storage_pool = storage_pool

    async def stream_upload(
        self,
        storage_name: str,
        bucket_name: str,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to upload
            content_type: Content type of the file
            data_stream: Async iterator of file data chunks
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        await storage.stream_upload(filepath, data_stream)

    async def stream_download(
        self, storage_name: str, bucket_name: str, filepath: str
    ) -> StreamReader:
        """
        Download a file from S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to download

        Returns:
            FileStream: Stream for reading file data
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        return await storage.stream_download(filepath)

    async def get_object_info(
        self, storage_name: str, bucket_name: str, filepath: str
    ) -> ObjectMetaResponse:
        """
        Get object information.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to download

        Returns:
            ObjectMetaResponse with object metadata
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        return await storage.get_object_info(filepath)

    async def delete_object(self, storage_name: str, bucket_name: str, prefix: str) -> None:
        """
        Delete an object and all its contents.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            prefix: Prefix of the object to delete
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        await storage.delete_object(prefix)

    async def generate_presigned_upload_url(
        self, storage_name: str, bucket_name: str, key: str
    ) -> PresignedUploadObjectResponse:
        """
        Generate presigned upload URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            key: Path to the file to upload

        Returns:
            PresignedUploadObjectResponse with URL and fields
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        return await storage.generate_presigned_upload_url(key)

    async def generate_presigned_download_url(
        self,
        storage_name: str,
        bucket_name: str,
        filepath: str,
    ) -> PresignedDownloadObjectResponse:
        """
        Generate presigned download URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to download

        Returns:
            PresignedDownloadResponse with URL
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        return await storage.generate_presigned_download_url(filepath)

    def _resolve_storage(self, storage_name: str, bucket_name: str) -> ObjectStorage:
        try:
            storage = self._storage_pool.get_storage(storage_name)
            if not isinstance(storage, ObjectStorage):
                raise StorageTypeInvalidError(f"Storage '{storage_name}' is not an ObjectStorage")

            # TODO: Remove this after supporting multiple buckets
            if storage._bucket != bucket_name:
                raise ObjectStorageBucketNotFoundError(
                    f"Bucket '{bucket_name}' not configured for storage '{storage_name}'. "
                    f"Expected bucket: '{storage._bucket}'"
                )

            return storage
        except KeyError:
            raise StorageNotFoundError(
                f"No storage configuration found for storage: {storage_name}"
            )
