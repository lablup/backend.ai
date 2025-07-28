import logging
from typing import AsyncIterator, Optional

import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError

from ai.backend.common.dto.storage.response import S3ObjectInfo, S3PresignedUploadData

logger = logging.getLogger(__name__)


class S3Client:
    """
    S3 client for file upload and download operations using aioboto3.
    """

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.session = aioboto3.Session()

    async def upload_stream(
        self,
        data_stream: AsyncIterator[bytes],
        s3_key: str,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
    ) -> bool:
        """
        Upload data stream to S3 bucket.

        Args:
            data_stream: Async iterator of bytes to upload
            s3_key: The S3 object key (destination path in bucket)
            content_type: MIME type of the file (optional)
            content_length: Total content length if known (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
                logger.info(f"Successfully uploaded stream to s3://{self.bucket_name}/{s3_key}")
                return True

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            logger.error(f"Failed to upload stream to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return False

    async def download_stream(
        self,
        s3_key: str,
        chunk_size: int = 8192,
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
        try:
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

                logger.info(f"Successfully streamed s3://{self.bucket_name}/{s3_key}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.error(f"S3 object not found: s3://{self.bucket_name}/{s3_key}")
            else:
                logger.error(f"Failed to stream file from S3: {e}")
            raise
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            raise

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        content_type: Optional[str] = None,
        content_length_range: Optional[tuple[int, int]] = None,
    ) -> Optional[S3PresignedUploadData]:
        """
        Generate a presigned URL for client-side upload to S3.

        Args:
            s3_key: The S3 object key for upload
            expiration: URL expiration time in seconds (default: 1 hour)
            content_type: Required content type for the upload (optional)
            content_length_range: Tuple of (min, max) content length in bytes (optional)

        Returns:
            S3PresignedUploadData: Presigned URL data or None if failed
        """
        try:
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

                logger.info(f"Generated presigned upload URL for s3://{self.bucket_name}/{s3_key}")
                return S3PresignedUploadData(
                    url=response["url"],
                    fields=response["fields"],
                    key=s3_key,
                )

        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned upload URL: {e}")
            return None

    async def generate_presigned_download_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        response_content_disposition: Optional[str] = None,
        response_content_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a presigned URL for client-side download from S3.

        Args:
            s3_key: The S3 object key to download
            expiration: URL expiration time in seconds (default: 1 hour)
            response_content_disposition: Override Content-Disposition header (optional)
            response_content_type: Override Content-Type header (optional)

        Returns:
            str: Presigned download URL or None if failed
        """
        try:
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

                logger.info(
                    f"Generated presigned download URL for s3://{self.bucket_name}/{s3_key}"
                )
                return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned download URL: {e}")
            return None

    async def get_object_info(self, s3_key: str) -> Optional[S3ObjectInfo]:
        """
        Get metadata information about an S3 object.

        Args:
            s3_key: The S3 object key

        Returns:
            S3ObjectInfo: Object metadata or None if object doesn't exist
        """
        try:
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
                return S3ObjectInfo(
                    content_length=response.get("ContentLength"),
                    content_type=response.get("ContentType"),
                    last_modified=last_modified.isoformat() if last_modified else None,
                    etag=response.get("ETag"),
                    metadata=response.get("Metadata", {}),
                )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("NoSuchKey", "404", "NotFound"):
                logger.debug(f"S3 object not found: s3://{self.bucket_name}/{s3_key}")
                return None
            else:
                logger.error(f"Failed to get object info from S3: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error getting object info: {e}")
            return None

    async def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3 bucket.

        Args:
            s3_key: The S3 object key to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
                logger.info(f"Successfully deleted s3://{self.bucket_name}/{s3_key}")
                return True

        except ClientError as e:
            logger.error(f"Failed to delete object from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            return False
