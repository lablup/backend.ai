from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Iterable, Optional, override

import aioboto3

from ai.backend.common.dto.storage.response import ObjectMetaResponse, PresignedUploadObjectResponse
from ai.backend.common.types import StreamReader

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _S3Credentials:
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]


@dataclass(frozen=True)
class _S3Target:
    bucket_name: str
    key: str
    endpoint_url: str
    region_name: Optional[str]


@dataclass(frozen=True)
class _S3DownloadConfig:
    chunk_size: int
    content_type: Optional[str]


class S3DownloadStreamReader(StreamReader):
    def __init__(
        self,
        target: _S3Target,
        credentials: _S3Credentials,
        config: _S3DownloadConfig,
    ):
        self._session = aioboto3.Session()
        self._target = target
        self._credentials = credentials
        self._config = config

    @override
    async def read(self) -> AsyncIterator[bytes]:
        async with self._session.client(
            "s3",
            endpoint_url=self._target.endpoint_url,
            region_name=self._target.region_name,
            aws_access_key_id=self._credentials.aws_access_key_id,
            aws_secret_access_key=self._credentials.aws_secret_access_key,
        ) as s3_client:
            response = await s3_client.get_object(
                Bucket=self._target.bucket_name,
                Key=self._target.key,
            )

            body = response["Body"]
            try:
                while True:
                    chunk = await body.read(self._config.chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                body.close()

    @override
    def content_type(self) -> Optional[str]:
        return self._config.content_type


class S3Client:
    """
    S3 client for file upload and download operations using aioboto3.
    """

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str,
        region_name: Optional[str],
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = aioboto3.Session()

    async def create_bucket(self, bucket_name: str) -> None:
        """
        Create an S3 bucket if it does not already exist.

        Args:
            bucket_name: Name of the bucket to create.
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            await s3_client.create_bucket(Bucket=bucket_name)

    async def delete_bucket(self, bucket_name: str) -> None:
        """
        Delete an S3 bucket if it exists.

        Args:
            bucket_name: Name of the bucket to delete.
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            await s3_client.delete_bucket(Bucket=bucket_name)

    async def upload_stream(
        self,
        data_stream: StreamReader,
        s3_key: str,
        part_size: int,
    ) -> None:
        """
        Upload data stream to S3 using streaming.

        Args:
            data_stream: StreamReader to upload
            s3_key: The S3 object key (destination path in bucket)
            part_size: Size of each part in bytes
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            create_args = {"Bucket": self.bucket_name, "Key": s3_key}
            if content_type := data_stream.content_type():
                create_args["ContentType"] = content_type

            resp = await s3_client.create_multipart_upload(**create_args)
            upload_id = resp["UploadId"]

            parts = []
            part_no = 1
            buf = bytearray()

            try:
                async for downloaded_chunk in data_stream.read():
                    if not downloaded_chunk:
                        continue
                    buf.extend(downloaded_chunk)

                    while len(buf) >= part_size:
                        piece = bytes(buf[:part_size])
                        del buf[:part_size]

                        upload_resp = await s3_client.upload_part(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            PartNumber=part_no,
                            UploadId=upload_id,
                            Body=piece,
                        )
                        parts.append({"PartNumber": part_no, "ETag": upload_resp["ETag"]})
                        part_no += 1

                if buf:
                    upload_resp = await s3_client.upload_part(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        PartNumber=part_no,
                        UploadId=upload_id,
                        Body=bytes(buf),
                    )
                    parts.append({"PartNumber": part_no, "ETag": upload_resp["ETag"]})

                await s3_client.complete_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )

            except Exception:
                try:
                    await s3_client.abort_multipart_upload(
                        Bucket=self.bucket_name, Key=s3_key, UploadId=upload_id
                    )
                finally:
                    # Reraise original exception, not abort exception
                    raise

    def download_stream(
        self,
        s3_key: str,
        chunk_size: int,
        content_type: Optional[str] = None,
    ) -> StreamReader:
        """
        Download and stream S3 object content as bytes chunks.
        This method streams the file content without downloading the entire file to memory.

        Args:
            s3_key: The S3 object key to download
            chunk_size: Size of each chunk in bytes

        Returns:
            FileStream: Stream for reading file data chunks
        """
        target = _S3Target(
            bucket_name=self.bucket_name,
            key=s3_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
        )
        credentials = _S3Credentials(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        config = _S3DownloadConfig(
            chunk_size=chunk_size,
            content_type=content_type,
        )

        return S3DownloadStreamReader(
            target=target,
            credentials=credentials,
            config=config,
        )

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        expiration: int,
        content_length_range: Optional[tuple[int, int]] = None,
    ) -> PresignedUploadObjectResponse:
        """
        Generate a presigned URL for client-side upload to S3.

        Args:
            s3_key: The S3 object key for upload
            expiration: URL expiration time in seconds
            content_length_range: Tuple of (min, max) content length in bytes (optional)

        Returns:
            PresignedUploadObjectResponse: Presigned URL data
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            conditions: list = []

            if content_length_range:
                conditions.append([
                    "content-length-range",
                    content_length_range[0],
                    content_length_range[1],
                ])

            response = await s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={},
                Conditions=conditions,
                ExpiresIn=expiration,
            )

            return PresignedUploadObjectResponse(
                url=response["url"],
                fields=response["fields"],
            )

    async def generate_presigned_download_url(
        self,
        s3_key: str,
        expiration: int,
        response_content_disposition: Optional[str] = None,
        response_content_type: Optional[str] = None,
    ) -> str:
        """
        Generate a presigned URL for client-side download from S3.

        Args:
            s3_key: The S3 object key to download
            expiration: URL expiration time in seconds
            response_content_disposition: Override Content-Disposition header (optional)
            response_content_type: Override Content-Type header (optional)

        Returns:
            str: Presigned download URL
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            params = {
                "Bucket": self.bucket_name,
                "Key": s3_key,
            }

            if response_content_disposition:
                params["ResponseContentDisposition"] = response_content_disposition
            if response_content_type:
                params["ResponseContentType"] = response_content_type

            url = await s3_client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiration,
            )

            return url

    async def get_object_meta(self, s3_key: str) -> ObjectMetaResponse:
        """
        Get metadata information about an S3 object.

        Args:
            s3_key: The S3 object key

        Returns:
            ObjectMetaResponse: Object metadata
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            response = await s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            last_modified = response.get("LastModified")
            return ObjectMetaResponse(
                content_length=response.get("ContentLength"),
                content_type=response.get("ContentType"),
                last_modified=last_modified.isoformat() if last_modified else None,
                etag=response.get("ETag"),
                metadata=response.get("Metadata", {}),
            )

    async def delete_object(
        self,
        key_or_prefix: str,
        *,
        delete_all_versions: bool = True,
        batch_size: int = 100,
    ) -> None:
        """
        Delete a single object or all objects under a given prefix ("folder").

        - If key_or_prefix ends with "/", treat as prefix deletion (folder)
        - Otherwise, treat as single object deletion

        Args:
            key_or_prefix: Either a specific object key or a prefix for multiple objects (ending with "/")
            delete_all_versions: Whether to delete all versions in versioned buckets
            batch_size: Number of objects to delete per batch
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3:
            # If key ends with "/", treat as prefix deletion (folder)
            if key_or_prefix.endswith("/"):
                norm_prefix = key_or_prefix
            else:
                # Single object deletion
                await s3.delete_object(Bucket=self.bucket_name, Key=key_or_prefix)
                return

            def _chunks(seq: list[Any], size: int) -> Iterable[list[Any]]:
                for i in range(0, len(seq), size):
                    return_chunk = seq[i : i + size]
                    if return_chunk:
                        yield return_chunk

            if delete_all_versions:
                # Remove all versions and delete markers under the prefix
                paginator = s3.get_paginator("list_object_versions")
                async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=norm_prefix):
                    to_delete: list[dict[str, str]] = []
                    for v in page.get("Versions", []):
                        to_delete.append({"Key": v["Key"], "VersionId": v["VersionId"]})
                    for m in page.get("DeleteMarkers", []):
                        to_delete.append({"Key": m["Key"], "VersionId": m["VersionId"]})

                    for chunk in _chunks(to_delete, batch_size):
                        await s3.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={"Objects": chunk, "Quiet": False},
                        )
                return

            # Non-versioned (or just current versions): list & batch-delete
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=norm_prefix):
                contents = page.get("Contents", [])
                if not contents:
                    continue
                keys = [{"Key": obj["Key"]} for obj in contents]
                for chunk in _chunks(keys, batch_size):
                    await s3.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={"Objects": chunk, "Quiet": False},
                    )

            # In case there's a standalone "directory marker" object like "prefix/"
            # (It may already have been removed above; this call is idempotent.)
            try:
                await s3.delete_object(Bucket=self.bucket_name, Key=norm_prefix)
            except Exception:
                # TODO: Improve exception handling
                # Ignore if it doesn't exist or bucket is not versioned / marker absent
                pass
