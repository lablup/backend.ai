import aioboto3
import pytest
from botocore.exceptions import ClientError

from ai.backend.storage.client.s3 import S3Client, S3ObjectInfo, S3PresignedUploadData
from ai.backend.testutils.bootstrap import minio_container  # noqa: F401


@pytest.fixture
async def s3_client(minio_container):  # noqa: F811
    """Create S3Client instance for testing with MinIO container"""
    container_id, host_port = minio_container

    client = S3Client(
        bucket_name="test-bucket",
        endpoint_url=f"http://{host_port.host}:{host_port.port}",
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )

    # Create test bucket
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=f"http://{host_port.host}:{host_port.port}",
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    ) as s3_admin:
        try:
            await s3_admin.create_bucket(Bucket="test-bucket")
        except ClientError as e:
            # Bucket might already exist
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise

    return client


@pytest.mark.asyncio
async def test_upload_stream_success(s3_client: S3Client):
    """Test successful stream upload"""

    async def data_stream():
        yield b"chunk1"
        yield b"chunk2"
        yield b"chunk3"

    result = await s3_client.upload_stream(data_stream(), "test/key.txt", content_type="text/plain")

    assert result is True

    # Verify the file was uploaded by downloading it
    chunks = []
    async for chunk in s3_client.download_stream("test/key.txt"):
        chunks.append(chunk)

    assert b"".join(chunks) == b"chunk1chunk2chunk3"


@pytest.mark.asyncio
async def test_download_stream_success(s3_client: S3Client):
    """Test successful stream download"""
    test_data = b"This is test file content"

    # First upload test data
    async def data_stream():
        yield test_data

    upload_result = await s3_client.upload_stream(data_stream(), "test/download.txt")
    assert upload_result is True

    # Now download and verify
    chunks = []
    async for chunk in s3_client.download_stream("test/download.txt"):
        chunks.append(chunk)

    assert b"".join(chunks) == test_data


@pytest.mark.asyncio
async def test_download_stream_not_found(s3_client: S3Client):
    """Test download stream with object not found"""
    with pytest.raises(ClientError) as exc_info:
        async for chunk in s3_client.download_stream("nonexistent/key.txt"):
            pass

    assert exc_info.value.response["Error"]["Code"] in ["NoSuchKey", "404"]


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_success(s3_client: S3Client):
    """Test successful presigned upload URL generation"""
    result = await s3_client.generate_presigned_upload_url(
        "test/presigned_upload.txt",
        expiration=3600,
        content_type="text/plain",
        content_length_range=(10, 1000),
    )

    assert result is not None
    assert isinstance(result, S3PresignedUploadData)
    assert result.url is not None
    assert result.key == "test/presigned_upload.txt"
    assert result.fields is not None
    assert isinstance(result.fields, dict)

    # Verify URL contains MinIO endpoint
    assert "127.0.0.1" in result.url or "localhost" in result.url


@pytest.mark.asyncio
async def test_generate_presigned_download_url_success(s3_client: S3Client):
    """Test successful presigned download URL generation"""
    # First upload a file to download
    test_data = b"File for presigned download test"

    async def data_stream():
        yield test_data

    await s3_client.upload_stream(data_stream(), "test/presigned_download.txt")

    # Generate presigned download URL
    result = await s3_client.generate_presigned_download_url(
        "test/presigned_download.txt", expiration=3600
    )

    assert result is not None
    assert isinstance(result, str)
    # Verify URL contains MinIO endpoint and key
    assert "127.0.0.1" in result or "localhost" in result
    assert "presigned_download.txt" in result


@pytest.mark.asyncio
async def test_get_object_info_success(s3_client: S3Client):
    """Test successful object info retrieval"""
    test_data = b"Test file content for object info"

    # Upload test file
    async def data_stream():
        yield test_data

    await s3_client.upload_stream(data_stream(), "test/info.txt", content_type="text/plain")

    # Get object info
    result = await s3_client.get_object_info("test/info.txt")

    assert result is not None
    assert isinstance(result, S3ObjectInfo)
    assert result.content_length == len(test_data)
    assert result.content_type == "text/plain"
    assert result.etag is not None
    assert result.last_modified is not None


@pytest.mark.asyncio
async def test_get_object_info_not_found(s3_client: S3Client):
    """Test object info retrieval with object not found"""
    result = await s3_client.get_object_info("nonexistent/key.txt")
    assert result is None


@pytest.mark.asyncio
async def test_delete_object_success(s3_client: S3Client):
    """Test successful object deletion"""
    # First upload a file to delete
    test_data = b"File to be deleted"

    async def data_stream():
        yield test_data

    await s3_client.upload_stream(data_stream(), "test/delete_me.txt")

    # Verify file exists
    info = await s3_client.get_object_info("test/delete_me.txt")
    assert info is not None

    # Delete the file
    result = await s3_client.delete_object("test/delete_me.txt")
    assert result is True

    # Verify file is gone
    info_after_delete = await s3_client.get_object_info("test/delete_me.txt")
    assert info_after_delete is None


@pytest.mark.asyncio
async def test_delete_object_nonexistent(s3_client: S3Client):
    """Test deletion of nonexistent object (should succeed in S3)"""
    # In S3, deleting a nonexistent object is considered successful
    result = await s3_client.delete_object("nonexistent/file.txt")
    assert result is True
