import logging
from typing import AsyncIterable, AsyncIterator

from botocore.exceptions import ClientError

from ai.backend.common.dto.storage.request import ObjectStorageTokenData
from ai.backend.common.dto.storage.response import (
    DeleteResponse,
    ObjectInfoResponse,
    PresignedDownloadResponse,
    PresignedUploadResponse,
    UploadResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ..client.s3 import S3Client
from ..exception import (
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageBucketFileNotFoundError,
    StorageBucketNotFoundError,
    StorageNotFoundError,
    StorageProxyError,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_TOKEN_DURATION = 1800  # Default token expiration time in seconds


class StoragesService:
    """
    Service class for S3 storage operations.
    """

    _storage_configs: dict[str, ObjectStorageConfig]

    def __init__(self, storage_configs: list[ObjectStorageConfig]) -> None:
        """
        Initialize the StoragesService.

        Args:
            storage_configs: List of storage configurations from context
        """
        self._storage_configs = {config.name: config for config in storage_configs}

    def _get_s3_client(self, storage_name: str, bucket_name: str) -> S3Client:
        """
        Get S3 client for the specified storage and bucket.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket

        Returns:
            S3Client instance configured for the bucket

        Raises:
            StorageNotFoundError: If no storage configuration found
            StorageBucketNotFoundError: If bucket not found in storage config
        """
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

    async def stream_upload(
        self,
        storage_name: str,
        bucket_name: str,
        token_data: ObjectStorageTokenData,
        data_stream: AsyncIterable[bytes],
    ) -> UploadResponse:
        """
        Upload a file to S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data
            data_stream: Async iterator of file data chunks

        Returns:
            UploadResponse with success status and key

        Raises:
            StorageProxyError: If upload fails
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            # Upload the stream
            await s3_client.upload_stream(
                data_stream,
                token_data.key,
                content_type=token_data.content_type,
            )

            # If we reach here, upload was successful
            return UploadResponse(success=True, key=token_data.key)

        except Exception as e:
            log.error(f"Stream upload failed: {e}")
            raise StorageProxyError("Upload failed") from e

    async def stream_download(
        self, storage_name: str, bucket_name: str, token_data: ObjectStorageTokenData
    ) -> AsyncIterator[bytes]:
        """
        Download a file from S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data

        Yields:
            bytes: Chunks of file data

        Raises:
            StorageProxyError: If download fails
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            # Download the stream
            async for chunk in s3_client.download_stream(token_data.key):
                yield chunk

        except Exception as e:
            log.error(f"Stream download failed: {e}")
            raise StorageProxyError("Download failed") from e

    async def generate_presigned_upload_url(
        self, storage_name: str, bucket_name: str, token_data: ObjectStorageTokenData
    ) -> PresignedUploadResponse:
        """
        Generate presigned upload URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data

        Returns:
            PresignedUploadResponse with URL and fields

        Raises:
            PresignedUploadURLGenerationError: If URL generation fails
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            presigned_data = await s3_client.generate_presigned_upload_url(
                token_data.key,
                expiration=token_data.expiration or _DEFAULT_TOKEN_DURATION,
                content_type=token_data.content_type,
                content_length_range=(token_data.min_size, token_data.max_size)
                if token_data.min_size and token_data.max_size
                else None,
            )

            if presigned_data is None:
                raise PresignedUploadURLGenerationError()

            return PresignedUploadResponse(url=presigned_data.url, fields=presigned_data.fields)

        except Exception as e:
            log.error(f"Presigned upload URL generation failed: {e}")
            raise PresignedUploadURLGenerationError() from e

    async def generate_presigned_download_url(
        self, storage_name: str, bucket_name: str, token_data: ObjectStorageTokenData
    ) -> PresignedDownloadResponse:
        """
        Generate presigned download URL.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data

        Returns:
            PresignedDownloadResponse with URL

        Raises:
            PresignedDownloadURLGenerationError: If URL generation fails
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)

            presigned_url = await s3_client.generate_presigned_download_url(
                token_data.key,
                expiration=token_data.expiration or _DEFAULT_TOKEN_DURATION,
            )

            if presigned_url is None:
                raise PresignedDownloadURLGenerationError()

            return PresignedDownloadResponse(url=presigned_url)

        except Exception as e:
            log.error(f"Presigned download URL generation failed: {e}")
            raise PresignedDownloadURLGenerationError() from e

    async def get_object_info(
        self, storage_name: str, bucket_name: str, token_data: ObjectStorageTokenData
    ) -> ObjectInfoResponse:
        """
        Get object information.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data

        Returns:
            ObjectInfoResponse with object metadata

        Raises:
            StorageObjectNotFoundError: If object not found
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            object_info = await s3_client.get_object_info(token_data.key)

            if object_info is None:
                raise StorageBucketFileNotFoundError()

            return ObjectInfoResponse(
                content_length=object_info.content_length,
                content_type=object_info.content_type,
                last_modified=object_info.last_modified,
                etag=object_info.etag,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404" or error_code == "NoSuchKey":
                raise StorageBucketFileNotFoundError() from e
            else:
                log.error(f"S3 client error in get_object_info: {e}")
                raise StorageProxyError(f"Failed to get object info: {str(e)}") from e

        except Exception as e:
            log.error(f"Get object info failed: {e}")
            raise StorageProxyError(f"Get object info failed: {str(e)}") from e

    async def delete_object(
        self, storage_name: str, bucket_name: str, token_data: ObjectStorageTokenData
    ) -> DeleteResponse:
        """
        Delete object.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            token_data: Validated object storage token data

        Returns:
            DeleteResponse with success status
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            await s3_client.delete_object(token_data.key)
            return DeleteResponse(success=True)

        except Exception as e:
            log.error(f"Delete object failed: {e}")
            return DeleteResponse(success=False)
