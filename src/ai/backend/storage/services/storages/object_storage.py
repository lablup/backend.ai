import logging
from typing import AsyncIterable, AsyncIterator, Optional

from ai.backend.common.dto.storage.response import (
    ObjectMetaResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import StorageBucketNotFoundError, StorageNotFoundError
from ai.backend.storage.storages.base import StoragePool
from ai.backend.storage.storages.object_storage import ObjectStorage

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
        content_type: Optional[str],
        data_stream: AsyncIterable[bytes],
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
        await storage.stream_upload(filepath, data_stream, content_type)

    async def stream_download(
        self, storage_name: str, bucket_name: str, filepath: str
    ) -> AsyncIterator[bytes]:
        """
        Download a file from S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to download

        Yields:
            bytes: Chunks of file data
        """
        storage = self._resolve_storage(storage_name, bucket_name)
        async for chunk in storage.stream_download(filepath):
            yield chunk

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

    def _resolve_storage(self, storage_name: str, bucket_name: str) -> ObjectStorage:
        try:
            storage = self._storage_pool.get_storage(storage_name)
            if not isinstance(storage, ObjectStorage):
                raise StorageNotFoundError(f"Storage '{storage_name}' is not an ObjectStorage")

            # TODO: Remove this after supporting multiple buckets
            if storage._bucket != bucket_name:
                raise StorageBucketNotFoundError(
                    f"Bucket '{bucket_name}' not configured for storage '{storage_name}'. "
                    f"Expected bucket: '{storage._bucket}'"
                )

            return storage
        except KeyError:
            raise StorageNotFoundError(
                f"No storage configuration found for storage: {storage_name}"
            )
