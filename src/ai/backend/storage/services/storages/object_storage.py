import logging
from typing import AsyncIterable, AsyncIterator, Optional

from ai.backend.common.dto.storage.request import PresignedUploadObjectReq
from ai.backend.common.dto.storage.response import (
    ObjectMetaResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ...client.s3 import S3Client
from ...exception import (
    FileStreamDownloadError,
    FileStreamUploadError,
    ObjectInfoFetchError,
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageBucketFileNotFoundError,
    StorageBucketNotFoundError,
    StorageNotFoundError,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_EXPIRATION = 1800  # Default token expiration time in seconds


class ObjectStorageService:
    """
    Service class for S3 storage operations.
    """

    _storage_configs: dict[str, ObjectStorageConfig]

    def __init__(self, storage_configs: list[ObjectStorageConfig]) -> None:
        self._storage_configs = {config.name: config for config in storage_configs}

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
        try:
            part_size = self._storage_configs[storage_name].upload_chunk_size
            s3_client = self._get_s3_client(storage_name, bucket_name)
            await s3_client.upload_stream(
                data_stream,
                filepath,
                content_type=content_type,
                part_size=part_size,
            )
        except Exception as e:
            raise FileStreamUploadError("Upload failed") from e

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
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            chunk_size = self._storage_configs[storage_name].download_chunk_size
            async for chunk in s3_client.download_stream(filepath, chunk_size=chunk_size):
                yield chunk

        except Exception as e:
            raise FileStreamDownloadError("Download failed") from e

    # TODO: Replace `request` with proper options
    async def generate_presigned_upload_url(
        self, storage_name: str, bucket_name: str, request: PresignedUploadObjectReq
    ) -> PresignedUploadObjectResponse:
        """
        Generate presigned upload URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            request: PresignedUploadReq containing key, content_type, expiration, min_size, max_size

        Returns:
            PresignedUploadObjectResponse with URL and fields
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            presigned_data = await s3_client.generate_presigned_upload_url(
                request.key,
                expiration=request.expiration or _DEFAULT_EXPIRATION,
                content_type=request.content_type,
                content_length_range=(request.min_size, request.max_size)
                if request.min_size and request.max_size
                else None,
            )

            if presigned_data is None:
                raise PresignedUploadURLGenerationError()

            # TODO: Separate PresignedUploadObjectResponse dto class
            return PresignedUploadObjectResponse(
                url=presigned_data.url, fields=presigned_data.fields
            )

        except Exception as e:
            raise PresignedUploadURLGenerationError() from e

    async def generate_presigned_download_url(
        self,
        storage_name: str,
        bucket_name: str,
        filepath: str,
        expiration: int = _DEFAULT_EXPIRATION,
    ) -> PresignedDownloadObjectResponse:
        """
        Generate presigned download URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to download
            expiration: Expiration time in seconds (default: 1800)

        Returns:
            PresignedDownloadResponse with URL
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            presigned_url = await s3_client.generate_presigned_download_url(
                filepath,
                expiration=expiration,
            )

            if presigned_url is None:
                raise PresignedDownloadURLGenerationError()

            return PresignedDownloadObjectResponse(url=presigned_url)

        except Exception as e:
            raise PresignedDownloadURLGenerationError() from e

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
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            object_info = await s3_client.get_object_meta(filepath)

            if object_info is None:
                raise StorageBucketFileNotFoundError()

            # TODO: Separate ObjectMetaResponse dto class
            return ObjectMetaResponse(
                content_length=object_info.content_length,
                content_type=object_info.content_type,
                last_modified=object_info.last_modified,
                etag=object_info.etag,
                metadata=object_info.metadata,
            )

        except Exception as e:
            raise ObjectInfoFetchError(f"Get object info failed: {str(e)}") from e

    async def delete_object(self, storage_name: str, bucket_name: str, prefix: str) -> None:
        """
        Delete an object and all its contents.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            prefix: Prefix of the object to delete
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            await s3_client.delete_object(prefix)
        except Exception as e:
            raise StorageBucketNotFoundError(f"Delete object failed: {str(e)}") from e

    def _get_s3_client(self, storage_name: str, bucket_name: str) -> S3Client:
        storage_config = self._storage_configs.get(storage_name)
        if not storage_config:
            raise StorageNotFoundError(
                f"No storage configuration found for storage: {storage_name}"
            )

        if bucket_name not in storage_config.buckets:
            raise StorageBucketNotFoundError(
                f"Bucket '{bucket_name}' not found in storage '{storage_name}'"
            )

        return S3Client(
            bucket_name=bucket_name,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )
