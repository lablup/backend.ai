"""
S3 Storage Service for Backend.AI Storage Proxy
"""

import logging
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator

from aiohttp import web
from botocore.exceptions import ClientError

from ai.backend.common.dto.storage.request import S3TokenData
from ai.backend.common.dto.storage.response import (
    DeleteResponse,
    ObjectInfoResponse,
    PresignedDownloadResponse,
    PresignedUploadResponse,
    UploadResponse,
)
from ai.backend.common.json import dump_json_str
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ..client.s3 import S3Client
from ..exception import (
    ExternalError,
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageObjectNotFoundError,
    StorageProxyError,
)
from ..utils import log_client_api_entry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_TOKEN_DURATION = 1800  # Default token expiration time in seconds


class StoragesService:
    """Service class for S3 storage operations."""

    def __init__(self, storage_configs: list[ObjectStorageConfig]) -> None:
        """
        Initialize the StoragesService.

        Args:
            storage_configs: List of storage configurations from context
        """
        self._storage_configs = {config.bucket: config for config in storage_configs}

    @actxmgr
    async def _handle_external_errors(self) -> AsyncIterator[None]:
        """Handle external errors and convert them to appropriate HTTP responses."""
        try:
            yield
        except ExternalError as e:
            log.exception("An external error occurred: %s", str(e))
            raise web.HTTPInternalServerError(
                text=dump_json_str({
                    "msg": "An internal error has occurred.",
                }),
                content_type="application/json",
            )

    def _get_s3_client(self, bucket_name: str) -> S3Client:
        """
        Get S3 client for the specified bucket.

        Args:
            bucket_name: Name of the S3 bucket

        Returns:
            S3Client instance configured for the bucket

        Raises:
            web.HTTPBadRequest: If no storage configuration found for bucket
        """
        storage_config = self._storage_configs.get(bucket_name)
        if not storage_config:
            raise web.HTTPBadRequest(
                reason=f"No storage configuration found for bucket: {bucket_name}"
            )

        return S3Client(
            bucket_name=bucket_name,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

    async def stream_upload(self, token_data: S3TokenData, data_stream) -> UploadResponse:
        """
        Upload a file to S3 using streaming.

        Args:
            token_data: Validated S3 token data
            data_stream: Async iterator of file data chunks

        Returns:
            UploadResponse with success status and key

        Raises:
            StorageProxyError: If upload fails
        """
        await log_client_api_entry(log, "stream_upload", token_data)

        try:
            s3_client = self._get_s3_client(token_data.bucket)

            # Upload the stream
            success = await s3_client.upload_stream(
                data_stream,
                token_data.key,
                content_type=token_data.content_type,
            )

            if success:
                return UploadResponse(success=True, key=token_data.key)
            else:
                raise StorageProxyError("Upload failed")

        except Exception as e:
            log.error(f"Stream upload failed: {e}")
            raise StorageProxyError("Upload failed") from e

    async def generate_presigned_upload_url(
        self, token_data: S3TokenData
    ) -> PresignedUploadResponse:
        """
        Generate presigned upload URL.

        Args:
            token_data: Validated S3 token data

        Returns:
            PresignedUploadResponse with URL and fields

        Raises:
            PresignedUploadURLGenerationError: If URL generation fails
        """
        await log_client_api_entry(log, "presigned_upload_url", token_data)

        try:
            async with self._handle_external_errors():
                s3_client = self._get_s3_client(token_data.bucket)

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
        self, token_data: S3TokenData
    ) -> PresignedDownloadResponse:
        """
        Generate presigned download URL.

        Args:
            token_data: Validated S3 token data

        Returns:
            PresignedDownloadResponse with URL

        Raises:
            PresignedDownloadURLGenerationError: If URL generation fails
        """
        await log_client_api_entry(log, "presigned_download_url", token_data)

        try:
            async with self._handle_external_errors():
                s3_client = self._get_s3_client(token_data.bucket)

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

    async def get_object_info(self, token_data: S3TokenData) -> ObjectInfoResponse:
        """
        Get object information.

        Args:
            token_data: Validated S3 token data

        Returns:
            ObjectInfoResponse with object metadata

        Raises:
            StorageObjectNotFoundError: If object not found
        """
        await log_client_api_entry(log, "get_object_info", token_data)

        try:
            s3_client = self._get_s3_client(token_data.bucket)
            print("token_data.key!", token_data.key)
            object_info = await s3_client.get_object_info(token_data.key)
            print("object_info!", object_info)

            if object_info is None:
                raise StorageObjectNotFoundError()

            return ObjectInfoResponse(
                content_length=object_info.content_length,
                content_type=object_info.content_type,
                last_modified=object_info.last_modified,
                etag=object_info.etag,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404" or error_code == "NoSuchKey":
                raise StorageObjectNotFoundError() from e
            else:
                log.error(f"S3 client error in get_object_info: {e}")
                raise StorageProxyError(f"Failed to get object info: {str(e)}") from e

        except Exception as e:
            log.error(f"Get object info failed: {e}")
            raise StorageProxyError(f"Get object info failed: {str(e)}") from e

    async def delete_object(self, token_data: S3TokenData) -> DeleteResponse:
        """
        Delete object.

        Args:
            token_data: Validated S3 token data

        Returns:
            DeleteResponse with success status
        """
        await log_client_api_entry(log, "delete_object", token_data)

        try:
            async with self._handle_external_errors():
                s3_client = self._get_s3_client(token_data.bucket)

                success = await s3_client.delete_object(token_data.key)

                return DeleteResponse(success=success)

        except Exception as e:
            log.error(f"Delete object failed: {e}")
            return DeleteResponse(success=False)
