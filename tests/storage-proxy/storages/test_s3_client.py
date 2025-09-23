from collections.abc import AsyncIterator
from typing import Optional

import pytest
from botocore.exceptions import ClientError

from ai.backend.common.types import StreamReader
from ai.backend.storage.client.s3 import S3Client


class TestStreamReader(StreamReader):
    def __init__(self, data_chunks: list[bytes]):
        self._data_chunks = data_chunks

    async def read(self) -> AsyncIterator[bytes]:
        for chunk in self._data_chunks:
            yield chunk

    def content_type(self) -> Optional[str]:
        return None


_DEFAULT_UPLOAD_STREAM_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MiB
_DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE = 8192


@pytest.mark.asyncio
async def test_upload_stream_success(s3_client: S3Client):
    """Test successful stream upload"""

    test_stream = TestStreamReader([b"chunk1", b"chunk2", b"chunk3"])

    await s3_client.upload_stream(
        test_stream,
        "test/key.txt",
        part_size=_DEFAULT_UPLOAD_STREAM_CHUNK_SIZE,
    )

    # Verify the file was uploaded by downloading it
    chunks = []
    download_stream = s3_client.download_stream("test/key.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE)
    async for chunk in download_stream.read():
        chunks.append(chunk)

    assert b"".join(chunks) == b"chunk1chunk2chunk3"


@pytest.mark.asyncio
async def test_download_stream_success(s3_client: S3Client):
    """Test successful stream download"""
    test_data = b"This is test file content"

    # First upload test data
    test_stream = TestStreamReader([test_data])

    await s3_client.upload_stream(
        test_stream, "test/download.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
    )

    # Now download and verify
    chunks = []
    download_stream = s3_client.download_stream(
        "test/download.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
    )
    async for chunk in download_stream.read():
        chunks.append(chunk)

    assert b"".join(chunks) == test_data


@pytest.mark.asyncio
async def test_download_stream_not_found(s3_client: S3Client):
    """Test download stream with object not found"""
    with pytest.raises(ClientError) as exc_info:
        download_stream = s3_client.download_stream(
            "nonexistent/key.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
        )
        async for chunk in download_stream.read():
            pass

    assert exc_info.value.response["Error"]["Code"] in ["NoSuchKey", "404"]


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_success(s3_client: S3Client):
    """Test successful presigned upload URL generation"""
    result = await s3_client.generate_presigned_upload_url(
        "test/presigned_upload.txt",
        expiration=3600,
        content_length_range=(10, 1000),
    )

    assert result is not None
    assert result.url is not None
    assert result.fields is not None
    assert isinstance(result.fields, dict)

    # Verify URL contains MinIO endpoint
    assert "127.0.0.1" in result.url or "localhost" in result.url


@pytest.mark.asyncio
async def test_generate_presigned_download_url_success(s3_client: S3Client):
    """Test successful presigned download URL generation"""
    # First upload a file to download
    test_data = b"File for presigned download test"

    test_stream = TestStreamReader([test_data])

    await s3_client.upload_stream(
        test_stream, "test/presigned_download.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
    )

    # Generate presigned download URL
    result = await s3_client.generate_presigned_download_url(
        "test/presigned_download.txt", expiration=3600
    )

    assert result is not None
    # Verify URL contains MinIO endpoint and key
    assert "127.0.0.1" in result or "localhost" in result
    assert "presigned_download.txt" in result


@pytest.mark.asyncio
async def test_get_object_info_success(s3_client: S3Client):
    """Test successful object info retrieval"""
    test_data = b"Test file content for object info"

    # Upload test file
    test_stream = TestStreamReader([test_data])

    await s3_client.upload_stream(test_stream, "test/info.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE)

    # Get object info
    result = await s3_client.get_object_meta("test/info.txt")

    assert result is not None
    assert result.content_length == len(test_data)
    assert result.content_type == "binary/octet-stream"
    assert result.etag is not None
    assert result.last_modified is not None


@pytest.mark.asyncio
async def test_get_object_info_not_found(s3_client: S3Client):
    """Test object info retrieval with object not found"""
    with pytest.raises(ClientError):
        await s3_client.get_object_meta("nonexistent/key.txt")


@pytest.mark.asyncio
async def test_delete_object_success(s3_client: S3Client):
    """Test successful object deletion"""
    # First upload a file to delete
    test_data = b"File to be deleted"

    test_stream = TestStreamReader([test_data])

    await s3_client.upload_stream(
        test_stream, "test/delete_me.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
    )

    # Verify file exists
    info = await s3_client.get_object_meta("test/delete_me.txt")
    assert info is not None

    # Delete the file
    await s3_client.delete_object("test/delete_me.txt")

    # Verify file is gone
    with pytest.raises(ClientError):
        await s3_client.get_object_meta("test/delete_me.txt")


@pytest.mark.asyncio
async def test_delete_object_nonexistent(s3_client: S3Client):
    """Test deletion of nonexistent object (should succeed in S3)"""
    # In S3, deleting a nonexistent object is considered successful
    await s3_client.delete_object("nonexistent/file.txt")


@pytest.mark.asyncio
async def test_delete_folder_success(s3_client: S3Client):
    """Test successful folder (prefix) deletion"""
    # Upload multiple files under a common prefix
    folder_prefix = "test/folder"
    files = [
        f"{folder_prefix}/file1.txt",
        f"{folder_prefix}/file2.txt",
        f"{folder_prefix}/subfolder/file3.txt",
        f"{folder_prefix}/subfolder/file4.txt",
    ]

    # Upload all files
    for file_key in files:
        test_data = f"Content of {file_key}".encode()

        test_stream = TestStreamReader([test_data])

        await s3_client.upload_stream(test_stream, file_key, _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE)

    # Verify all files exist
    for file_key in files:
        info = await s3_client.get_object_meta(file_key)
        assert info is not None

    # Delete the entire folder
    await s3_client.delete_object(f"{folder_prefix}/", delete_all_versions=False)

    # Verify all files under the prefix are gone
    for file_key in files:
        with pytest.raises(ClientError):
            await s3_client.get_object_meta(file_key)


@pytest.mark.asyncio
async def test_delete_folder_empty(s3_client: S3Client) -> None:
    """Test deletion of empty folder (prefix with no objects)"""
    # Try to delete a non-existent folder prefix
    # Should not raise an exception even if nothing was deleted
    await s3_client.delete_object("empty/folder/")


@pytest.mark.asyncio
async def test_create_bucket_success(s3_client: S3Client):
    """Test successful bucket creation"""
    test_bucket_name = "test-create-bucket-new"

    # Create the bucket
    await s3_client.create_bucket(test_bucket_name)

    # Verify bucket was created by trying to list it or perform an operation
    # Since S3Client doesn't have a list_buckets method, we'll verify by uploading to it
    try:
        test_stream = TestStreamReader([b"test data"])

        # Create a new client instance for the test bucket
        test_client = S3Client(
            bucket_name=test_bucket_name,
            endpoint_url=s3_client.endpoint_url,
            region_name=s3_client.region_name,
            aws_access_key_id=s3_client.aws_access_key_id,
            aws_secret_access_key=s3_client.aws_secret_access_key,
        )

        # This should succeed if bucket was created
        await test_client.upload_stream(
            test_stream, "test-key.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
        )

        # Clean up the uploaded object first
        await test_client.delete_object("test-key.txt")

    finally:
        # Clean up: delete the test bucket
        try:
            await s3_client.delete_bucket(test_bucket_name)
        except Exception:
            pass  # Ignore errors during cleanup


@pytest.mark.asyncio
async def test_create_bucket_already_exists(s3_client: S3Client):
    """Test creating a bucket that already exists (should not fail)"""
    # The s3_client fixture already has a "test-bucket" created
    # Creating it again should handle the error gracefully
    try:
        await s3_client.create_bucket("test-bucket")
    except Exception:
        pass  # Expected to fail since bucket already exists

    # Verify the bucket still works
    test_stream = TestStreamReader([b"test data for existing bucket"])

    await s3_client.upload_stream(
        test_stream, "test-existing-bucket.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
    )


@pytest.mark.asyncio
async def test_delete_bucket_success(s3_client: S3Client):
    """Test successful bucket deletion"""
    test_bucket_name = "test-delete-bucket-new"

    # First create a bucket to delete
    await s3_client.create_bucket(test_bucket_name)

    # Delete the bucket (must be empty first)
    await s3_client.delete_bucket(test_bucket_name)

    # Verify bucket was deleted by trying to use it
    test_client = S3Client(
        bucket_name=test_bucket_name,
        endpoint_url=s3_client.endpoint_url,
        region_name=s3_client.region_name,
        aws_access_key_id=s3_client.aws_access_key_id,
        aws_secret_access_key=s3_client.aws_secret_access_key,
    )

    test_stream = TestStreamReader([b"test data"])

    # This should raise an exception since bucket doesn't exist
    with pytest.raises(ClientError):
        await test_client.upload_stream(
            test_stream, "test-key.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
        )


@pytest.mark.asyncio
async def test_delete_bucket_nonexistent(s3_client: S3Client):
    """Test deletion of nonexistent bucket (should handle error gracefully)"""
    # Deleting a nonexistent bucket will raise an error in MinIO/S3
    try:
        await s3_client.delete_bucket("nonexistent-bucket-12345")
    except ClientError:
        pass  # Expected to fail for nonexistent bucket
