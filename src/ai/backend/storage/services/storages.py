import asyncio
import logging
import mimetypes
from typing import AsyncIterable, AsyncIterator, Optional

import aioboto3
import aiohttp

from ai.backend.common.dto.storage.request import PresignedUploadObjectReq
from ai.backend.common.dto.storage.response import (
    DeleteObjectResponse,
    ObjectMetaResponse,
    PresignedDownloadObjectResponse,
    PresignedUploadObjectResponse,
    UploadObjectResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.config.unified import ObjectStorageConfig

from ..client.s3 import S3Client
from ..exception import (
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

CHUNK_SIZE = 1024 * 1024


def _is_dir_marker(key: str) -> bool:
    # 일부 도구가 "prefix/" 형태의 빈 오브젝트(디렉터리 마커)를 만들기도 함
    return key.endswith("/")


def _norm_prefix(prefix: Optional[str]) -> str:
    if not prefix:
        return ""
    return prefix if prefix.endswith("/") else f"{prefix}/"


class StorageService:
    """
    Service class for S3 storage operations.
    """

    _storage_configs: dict[str, ObjectStorageConfig]

    def __init__(self, storage_configs: list[ObjectStorageConfig]) -> None:
        """
        Initialize the StoragesService.

        Args:
            storage_configs: List of storage configurations
        """
        self._storage_configs = {config.name: config for config in storage_configs}

    async def stream_upload(
        self,
        storage_name: str,
        bucket_name: str,
        filepath: str,
        content_type: Optional[str],
        data_stream: AsyncIterable[bytes],
    ) -> UploadObjectResponse:
        """
        Upload a file to S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path to the file to upload
            content_type: Content type of the file
            data_stream: Async iterator of file data chunks

        Returns:
            UploadObjectResponse
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

            return UploadObjectResponse()
        except Exception as e:
            log.error(f"Stream upload failed: {e}")
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
            log.error(f"Stream download failed: {e}")
            raise FileStreamDownloadError("Download failed") from e

    async def stream_bucket_to_bucket(
        self,
        *,
        # ---- Source (MinIO/S3) connection params ----
        src_endpoint_url: str,
        src_access_key: str,
        src_secret_key: str,
        src_region: Optional[str],
        src_bucket_name: str,
        src_prefix: Optional[str] = None,  # 소스 프리픽스 (없으면 전체)
        # ---- Destination (existing wrapper) ----
        dst_storage_name: str,
        dst_bucket_name: str,
        dst_prefix: Optional[str] = None,  # 대상에 붙일 접두사
        # ---- Options ----
        concurrency: int = 16,
        part_size: Optional[int] = None,  # dst 멀티파트 사이즈(없으면 스토리지 설정)
        override_content_type: Optional[str] = None,
        read_chunk_size: int = CHUNK_SIZE,
    ) -> int:
        """
        소스 MinIO/S3(프리픽스 선택 가능) → 대상 버킷으로 스트리밍 복사.

        Args:
            src_endpoint_url: 소스 S3/MinIO 엔드포인트 (예: "http://127.0.0.1:9000")
            src_access_key: 소스 액세스 키
            src_secret_key: 소스 시크릿 키
            src_region: 소스 리전 (None 가능; MinIO는 보통 None/빈 문자열 가능)
            src_bucket_name: 소스 버킷 이름
            src_prefix: 복사할 프리픽스 (없으면 버킷 전체)
            dst_storage_name: 대상 스토리지 이름(내부 래퍼 조회용)
            dst_bucket_name: 대상 버킷 이름
            dst_prefix: 대상 접두사(없으면 소스 상대 경로 그대로)
            concurrency: 동시에 복사할 개수
            part_size: 대상 업로드 멀티파트 파트 크기
            override_content_type: 콘텐츠 타입 강제 설정
            read_chunk_size: 소스에서 읽을 스트림 청크 크기

        Returns:
            복사된 오브젝트(파일) 개수
        """
        # 대상 업로드 클라이언트/설정
        dst = self._get_s3_client(dst_storage_name, dst_bucket_name)
        if part_size is None:
            part_size = self._storage_configs[dst_storage_name].upload_chunk_size

        src_norm = _norm_prefix(src_prefix)
        dst_norm = _norm_prefix(dst_prefix)

        copied = 0
        sem = asyncio.Semaphore(concurrency)

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=src_endpoint_url,
            region_name=src_region,
            aws_access_key_id=src_access_key,
            aws_secret_access_key=src_secret_key,
        ) as src_s3:
            keys: list[str] = []
            paginator = src_s3.get_paginator("list_objects_v2")
            paginate_kwargs = {"Bucket": src_bucket_name}
            if src_norm:
                paginate_kwargs["Prefix"] = src_norm

            async for page in paginator.paginate(**paginate_kwargs):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if not _is_dir_marker(key):
                        keys.append(key)

            # 2) 개별 복사 태스크
            async def _copy_one(key: str) -> None:
                async with sem:
                    resp = await src_s3.get_object(Bucket=src_bucket_name, Key=key)
                    body = resp["Body"]

                    # 대상 키: dst_prefix + (src_prefix 이후 상대경로)
                    rel = key[len(src_norm) :] if src_norm and key.startswith(src_norm) else key
                    dst_key = f"{dst_norm}{rel}" if dst_norm else rel

                    ctype = (
                        override_content_type
                        or resp.get("ContentType")
                        or mimetypes.guess_type(key)[0]
                        or "application/octet-stream"
                    )

                    async def _gen() -> AsyncIterator[bytes]:
                        while True:
                            chunk = await body.read(read_chunk_size)
                            if not chunk:
                                break
                            yield chunk

                    await dst.upload_stream(
                        _gen(),
                        dst_key,
                        content_type=ctype,
                        part_size=part_size,
                    )

            if keys:
                await asyncio.gather(*(_copy_one(k) for k in keys))
            copied = len(keys)

        return copied

    async def stream_from_url(
        self,
        storage_name: str,
        bucket_name: str,
        filepath: str,
        url: str,
        content_type: Optional[str] = None,
    ) -> UploadObjectResponse:
        """
        Download a file from URL and upload it to S3 using streaming.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path where to store the file in the bucket
            url: URL to download the file from
            content_type: Content type of the file

        Returns:
            UploadObjectResponse
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            part_size = self._storage_configs[storage_name].upload_chunk_size

            async def url_stream() -> AsyncIterator[bytes]:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()

                        # Auto-detect content type if not provided
                        detected_content_type = content_type
                        if not detected_content_type:
                            detected_content_type = response.headers.get(
                                "content-type", "application/octet-stream"
                            )

                        async for chunk in response.content.iter_chunked(part_size):
                            yield chunk

            await s3_client.upload_stream(
                url_stream(),
                filepath,
                content_type=content_type,
                part_size=part_size,
            )

            return UploadObjectResponse()

        except Exception as e:
            log.error(f"Stream from URL failed: {e}")
            raise FileStreamUploadError("URL streaming failed") from e

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
            log.error(f"Presigned upload URL generation failed: {e}")
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
            log.error(f"Presigned download URL generation failed: {e}")
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

    async def delete_file(
        self, storage_name: str, bucket_name: str, filepath: str
    ) -> DeleteObjectResponse:
        """
        Delete file (object).

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path of the file to delete

        Returns:
            DeleteResponse with success status
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            await s3_client.delete_object(filepath)
            return DeleteObjectResponse()

        except Exception as e:
            log.error(f"Delete object failed: {e}")
            raise StorageBucketNotFoundError(f"Delete object failed: {str(e)}") from e

    async def delete_folder(
        self, storage_name: str, bucket_name: str, prefix: str
    ) -> DeleteObjectResponse:
        """
        Delete folder and all its contents.

        Args:
            storage_name: Name of the storage configuration
            bucket_name: Name of the S3 bucket
            filepath: Path of the file to delete

        Returns:
            DeleteResponse with success status
        """
        try:
            s3_client = self._get_s3_client(storage_name, bucket_name)
            await s3_client.delete_folder(prefix)
            return DeleteObjectResponse()

        except Exception as e:
            log.error(f"Delete folder failed: {e}")
            raise StorageBucketNotFoundError(f"Delete folder failed: {str(e)}") from e

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
