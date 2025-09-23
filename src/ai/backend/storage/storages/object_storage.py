import mimetypes
from typing import override

from ai.backend.common.dto.storage.response import (
    ObjectMetaResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
)
from ai.backend.common.types import StreamReader
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.unified import (
    ObjectStorageConfig,
    PresignedDownloadConfig,
    PresignedUploadConfig,
)
from ai.backend.storage.exception import (
    FileStreamDownloadError,
    FileStreamUploadError,
    ObjectInfoFetchError,
    ObjectStorageObjectDeletionError,
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageBucketFileNotFoundError,
)
from ai.backend.storage.storages.base import AbstractStorage


class ObjectStorage(AbstractStorage):
    _name: str
    _endpoint: str
    _access_key: str
    _secret_key: str
    _bucket: str
    _region: str
    _upload_chunk_size: int
    _download_chunk_size: int
    _reservoir_download_chunk_size: int
    _presigned_upload_config: PresignedUploadConfig
    _presigned_download_config: PresignedDownloadConfig

    def __init__(self, name: str, cfg: ObjectStorageConfig) -> None:
        self._name = name
        self._endpoint = cfg.endpoint
        self._access_key = cfg.access_key
        self._secret_key = cfg.secret_key
        self._bucket = cfg.buckets[0]
        self._region = cfg.region
        self._upload_chunk_size = cfg.upload_chunk_size
        self._download_chunk_size = cfg.download_chunk_size
        self._reservoir_download_chunk_size = cfg.reservoir_download_chunk_size
        self._presigned_upload_config = cfg.presigned_upload
        self._presigned_download_config = cfg.presigned_download

    @override
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        """
        Upload a file to S3 using streaming.

        Args:
            filepath: Path to the file to upload
            data_stream: Async iterator of file data chunks
            content_type: Content type of the file
        """
        try:
            part_size = self._upload_chunk_size
            s3_client = self._get_s3_client()
            await s3_client.upload_stream(
                data_stream,
                filepath,
                part_size=part_size,
            )
        except Exception as e:
            raise FileStreamUploadError("Upload failed") from e

    @override
    async def stream_download(self, filepath: str) -> StreamReader:
        """
        Download a file from S3 using streaming.

        Args:
            filepath: Path to the file to download

        Returns:
            FileStream: Stream for reading file data
        """
        try:
            s3_client = self._get_s3_client()
            object_meta = await s3_client.get_object_meta(filepath)
            ctype = (
                (object_meta.content_type if object_meta else None)
                or mimetypes.guess_type(filepath)[0]
                or "application/octet-stream"
            )
            chunk_size = self._download_chunk_size
            return s3_client.download_stream(filepath, chunk_size=chunk_size, content_type=ctype)

        except Exception as e:
            raise FileStreamDownloadError("Download failed") from e

    async def generate_presigned_upload_url(self, key: str) -> PresignedUploadObjectResponse:
        """
        Generate presigned upload URL.

        Args:
            key: Path to the file to upload

        Returns:
            PresignedUploadObjectResponse with URL and fields
        """
        try:
            s3_client = self._get_s3_client()
            presigned_upload_config = self._presigned_upload_config

            presigned_data = await s3_client.generate_presigned_upload_url(
                key,
                expiration=presigned_upload_config.expiration,
                content_length_range=(
                    presigned_upload_config.min_size,
                    presigned_upload_config.max_size,
                )
                if presigned_upload_config.min_size and presigned_upload_config.max_size
                else None,
            )

            if presigned_data is None:
                raise PresignedUploadURLGenerationError()

            return PresignedUploadObjectResponse(
                url=presigned_data.url, fields=presigned_data.fields
            )

        except Exception as e:
            raise PresignedUploadURLGenerationError() from e

    async def generate_presigned_download_url(
        self,
        filepath: str,
    ) -> PresignedDownloadObjectResponse:
        """
        Generate presigned download URL.

        Args:
            filepath: Path to the file to download

        Returns:
            PresignedDownloadResponse with URL
        """
        try:
            s3_client = self._get_s3_client()

            presigned_url = await s3_client.generate_presigned_download_url(
                filepath,
                expiration=self._presigned_download_config.expiration,
            )

            if presigned_url is None:
                raise PresignedDownloadURLGenerationError()

            return PresignedDownloadObjectResponse(url=presigned_url)

        except Exception as e:
            raise PresignedDownloadURLGenerationError() from e

    async def get_object_info(self, filepath: str) -> ObjectMetaResponse:
        """
        Get object information.

        Args:
            filepath: Path to the file to download

        Returns:
            ObjectMetaResponse with object metadata
        """
        try:
            s3_client = self._get_s3_client()
            object_info = await s3_client.get_object_meta(filepath)

            if object_info is None:
                raise StorageBucketFileNotFoundError()

            return ObjectMetaResponse(
                content_length=object_info.content_length,
                content_type=object_info.content_type,
                last_modified=object_info.last_modified,
                etag=object_info.etag,
                metadata=object_info.metadata,
            )

        except Exception as e:
            raise ObjectInfoFetchError(f"Get object info failed: {str(e)}") from e

    async def delete_object(self, prefix: str) -> None:
        """
        Delete an object and all its contents.

        Args:
            prefix: Prefix of the object to delete
        """
        try:
            s3_client = self._get_s3_client()
            await s3_client.delete_object(prefix)
        except Exception as e:
            raise ObjectStorageObjectDeletionError(f"Delete object failed: {str(e)}") from e

    def _get_s3_client(self) -> S3Client:
        return S3Client(
            bucket_name=self._bucket,
            endpoint_url=self._endpoint,
            region_name=self._region,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )
