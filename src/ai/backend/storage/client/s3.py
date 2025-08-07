import logging
from collections.abc import AsyncIterable
from typing import AsyncIterator, Optional

import aioboto3

from ai.backend.common.dto.storage.response import ObjectMetaResponse, PresignedUploadObjectResponse

logger = logging.getLogger(__name__)

_DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE = 8192  # Default chunk size for streaming downloads


class S3Client:
    """
    S3 client for file upload and download operations using aioboto3.
    """

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str,
        region_name: str,
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
        data_stream: AsyncIterable[bytes],
        s3_key: str,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
    ) -> None:
        """
        Upload data stream to S3 bucket.

        Args:
            data_stream: Async iterator of bytes to upload
            s3_key: The S3 object key (destination path in bucket)
            content_type: MIME type of the file (optional)
            content_length: Total content length if known (optional)
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            # For streaming upload, we need to use put_object with data
            data_chunks = []
            async for chunk in data_stream:
                data_chunks.append(chunk)

            data = b"".join(data_chunks)

            put_object_args = {
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "Body": data,
            }

            if content_type:
                put_object_args["ContentType"] = content_type
            if content_length:
                put_object_args["ContentLength"] = str(content_length)

            await s3_client.put_object(**put_object_args)

    async def download_stream(
        self,
        s3_key: str,
        chunk_size: int = _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE,
    ) -> AsyncIterator[bytes]:
        """
        Download and stream S3 object content as bytes chunks.
        This method streams the file content without downloading the entire file to memory.

        Args:
            s3_key: The S3 object key to download
            chunk_size: Size of each chunk in bytes

        Yields:
            bytes: Chunks of file content
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            response = await s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )

            body = response["Body"]
            try:
                while True:
                    chunk = await body.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            finally:
                body.close()

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        expiration: int,
        content_type: Optional[str] = None,
        content_length_range: Optional[tuple[int, int]] = None,
    ) -> PresignedUploadObjectResponse:
        """
        Generate a presigned URL for client-side upload to S3.

        Args:
            s3_key: The S3 object key for upload
            expiration: URL expiration time in seconds
            content_type: Required content type for the upload (optional)
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
            fields = {}

            if content_type:
                conditions.append({"Content-Type": content_type})
                fields["Content-Type"] = content_type

            if content_length_range:
                conditions.append([
                    "content-length-range",
                    content_length_range[0],
                    content_length_range[1],
                ])

            response = await s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
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

    async def delete_object(self, s3_key: str) -> None:
        """
        Delete an object from S3 bucket.

        Args:
            s3_key: The S3 object key to delete
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3_client:
            await s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
