import pytest
from botocore.exceptions import ClientError

from ai.backend.storage.client.s3 import S3Client

_DEFAULT_UPLOAD_STREAM_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MiB
_DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE = 8192


@pytest.mark.asyncio
async def test_upload_stream_success(s3_client: S3Client):
    """Test successful stream upload"""

    async def data_stream():
        yield b"chunk1"
        yield b"chunk2"
        yield b"chunk3"

    await s3_client.upload_stream(
        data_stream(),
        "test/key.txt",
        part_size=_DEFAULT_UPLOAD_STREAM_CHUNK_SIZE,
        content_type="text/plain",
    )

    # Verify the file was uploaded by downloading it
    chunks = []
    async for chunk in s3_client.download_stream(
        "test/key.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
    ):
        chunks.append(chunk)

    assert b"".join(chunks) == b"chunk1chunk2chunk3"


@pytest.mark.asyncio
async def test_download_stream_success(s3_client: S3Client):
    """Test successful stream download"""
    test_data = b"This is test file content"

    # First upload test data
    async def data_stream():
        yield test_data

    await s3_client.upload_stream(
        data_stream(), "test/download.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
    )

    # Now download and verify
    chunks = []
    async for chunk in s3_client.download_stream(
        "test/download.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
    ):
        chunks.append(chunk)

    assert b"".join(chunks) == test_data


@pytest.mark.asyncio
async def test_download_stream_not_found(s3_client: S3Client):
    """Test download stream with object not found"""
    with pytest.raises(ClientError) as exc_info:
        async for chunk in s3_client.download_stream(
            "nonexistent/key.txt", _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
        ):
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

    async def data_stream():
        yield test_data

    await s3_client.upload_stream(
        data_stream(), "test/presigned_download.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
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
    async def data_stream():
        yield test_data

    await s3_client.upload_stream(
        data_stream(), "test/info.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE, content_type="text/plain"
    )

    # Get object info
    result = await s3_client.get_object_meta("test/info.txt")

    assert result is not None
    assert result.content_length == len(test_data)
    assert result.content_type == "text/plain"
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

    async def data_stream():
        yield test_data

    await s3_client.upload_stream(
        data_stream(), "test/delete_me.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
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
async def test_create_bucket_success(s3_client: S3Client):
    """Test successful bucket creation"""
    test_bucket_name = "test-create-bucket-new"

    # Create the bucket
    await s3_client.create_bucket(test_bucket_name)

    # Verify bucket was created by trying to list it or perform an operation
    # Since S3Client doesn't have a list_buckets method, we'll verify by uploading to it
    try:

        async def data_stream():
            yield b"test data"

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
            data_stream(), "test-key.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
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
    async def data_stream():
        yield b"test data for existing bucket"

    await s3_client.upload_stream(
        data_stream(), "test-existing-bucket.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
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

    async def data_stream():
        yield b"test data"

    # This should raise an exception since bucket doesn't exist
    with pytest.raises(ClientError):
        await test_client.upload_stream(
            data_stream(), "test-key.txt", _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE
        )


@pytest.mark.asyncio
async def test_delete_bucket_nonexistent(s3_client: S3Client):
    """Test deletion of nonexistent bucket (should handle error gracefully)"""
    # Deleting a nonexistent bucket will raise an error in MinIO/S3
    try:
        await s3_client.delete_bucket("nonexistent-bucket-12345")
    except ClientError:
        pass  # Expected to fail for nonexistent bucket


@pytest.mark.asyncio
async def test_bucket_to_bucket_copy_simulation(s3_client: S3Client):
    """Test bucket-to-bucket copy simulation using S3Client methods (simulating pull_bucket functionality)"""
    import uuid

    source_bucket = "source-bucket-test"
    dest_bucket = "dest-bucket-test"
    test_suffix = str(uuid.uuid4())[:8]

    # Test files to copy
    test_files = [
        (f"copy_test_{test_suffix}_file1.txt", b"content of source file 1"),
        (f"copy_test_{test_suffix}_file2.txt", b"content of source file 2"),
        (f"copy_test_{test_suffix}_subdir/file3.txt", b"content of source file 3 in subdir"),
    ]

    try:
        # Create source and destination buckets
        await s3_client.create_bucket(source_bucket)
        await s3_client.create_bucket(dest_bucket)

        # Create source client
        source_client = S3Client(
            bucket_name=source_bucket,
            endpoint_url=s3_client.endpoint_url,
            region_name=s3_client.region_name,
            aws_access_key_id=s3_client.aws_access_key_id,
            aws_secret_access_key=s3_client.aws_secret_access_key,
        )

        # Create destination client
        dest_client = S3Client(
            bucket_name=dest_bucket,
            endpoint_url=s3_client.endpoint_url,
            region_name=s3_client.region_name,
            aws_access_key_id=s3_client.aws_access_key_id,
            aws_secret_access_key=s3_client.aws_secret_access_key,
        )

        # Upload test files to source bucket
        for key, content in test_files:

            async def content_stream():
                yield content

            await source_client.upload_stream(
                content_stream(),
                key,
                _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE,
                content_type="text/plain",
            )

        # Simulate bucket-to-bucket copy (what stream_bucket_to_bucket does)
        for key, expected_content in test_files:
            # Download from source
            chunks = []
            async for chunk in source_client.download_stream(
                key, _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
            ):
                chunks.append(chunk)

            downloaded_content = b"".join(chunks)
            assert downloaded_content == expected_content

            # Upload to destination
            async def copy_stream():
                yield downloaded_content

            await dest_client.upload_stream(
                copy_stream(),
                key,
                _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE,
                content_type="text/plain",
            )

            # Verify file exists in destination
            dest_info = await dest_client.get_object_meta(key)
            assert dest_info.content_length == len(expected_content)

            # Double check by downloading from destination
            dest_chunks = []
            async for chunk in dest_client.download_stream(
                key, _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE
            ):
                dest_chunks.append(chunk)

            dest_content = b"".join(dest_chunks)
            assert dest_content == expected_content

    finally:
        # Clean up: delete all objects and buckets
        try:
            # Delete objects from source bucket
            for key, _ in test_files:
                try:
                    await source_client.delete_object(key)
                except Exception:
                    pass

            # Delete objects from dest bucket
            for key, _ in test_files:
                try:
                    await dest_client.delete_object(key)
                except Exception:
                    pass

            # Delete buckets
            await s3_client.delete_bucket(source_bucket)
            await s3_client.delete_bucket(dest_bucket)
        except Exception:
            pass  # Ignore cleanup errors


@pytest.mark.asyncio
async def test_multiple_files_batch_operations(s3_client: S3Client):
    """Test batch operations on multiple files (used by pull_bucket functionality)"""
    import uuid

    test_suffix = str(uuid.uuid4())[:8]
    test_files = [
        (f"batch_test_{test_suffix}_file1.txt", b"batch test content 1"),
        (f"batch_test_{test_suffix}_file2.txt", b"batch test content 2"),
        (f"batch_test_{test_suffix}_file3.txt", b"batch test content 3"),
    ]

    try:
        # Upload multiple files
        for key, content in test_files:

            async def content_stream():
                yield content

            await s3_client.upload_stream(
                content_stream(),
                key,
                _DEFAULT_UPLOAD_STREAM_CHUNK_SIZE,
                content_type="text/plain",
            )

        # Verify all files exist and have correct content
        for key, expected_content in test_files:
            # Check metadata
            info = await s3_client.get_object_meta(key)
            assert info.content_length == len(expected_content)

            # Check content
            chunks = []
            async for chunk in s3_client.download_stream(key, _DEFAULT_DOWNLOAD_STREAM_CHUNK_SIZE):
                chunks.append(chunk)

            actual_content = b"".join(chunks)
            assert actual_content == expected_content

        # Batch delete all files
        for key, _ in test_files:
            await s3_client.delete_object(key)

        # Verify all files are deleted
        for key, _ in test_files:
            with pytest.raises(ClientError):
                await s3_client.get_object_meta(key)

    finally:
        # Cleanup in case of test failure
        for key, _ in test_files:
            try:
                await s3_client.delete_object(key)
            except Exception:
                pass
