import uuid

import pytest

from ai.backend.common.dto.storage.request import ObjectStorageOperationType, ObjectStorageTokenData
from ai.backend.common.dto.storage.response import (
    DeleteResponse,
    ObjectInfoResponse,
    PresignedDownloadResponse,
    PresignedUploadResponse,
    UploadResponse,
)
from ai.backend.storage.config.unified import ObjectStorageConfig
from ai.backend.storage.exception import (
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageBucketFileNotFoundError,
    StorageBucketNotFoundError,
    StorageNotFoundError,
    StorageProxyError,
)
from ai.backend.storage.services.storages import StoragesService

UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")

_BUCKET_FIXTURE_NAME = "test-bucket"


@pytest.fixture
def storage_config(minio_container):
    container_id, host_port = minio_container
    return ObjectStorageConfig(
        name="test_storage",
        buckets=[_BUCKET_FIXTURE_NAME],
        endpoint=f"http://{host_port.host}:{host_port.port}",
        region="us-east-1",
        access_key="minioadmin",
        secret_key="minioadmin",
    )


@pytest.fixture
def storages_service(storage_config):
    return StoragesService([storage_config])


@pytest.fixture
def valid_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.UPLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key="test-key",
        expiration=3600,
        content_type="application/octet-stream",
        filename="test-file.txt",
    )


@pytest.fixture
def download_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.DOWNLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key="test-key",
        expiration=3600,
        content_type="application/octet-stream",
        filename="test-file.txt",
    )


@pytest.fixture
def presigned_upload_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.PRESIGNED_UPLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key="presigned-test-key",
        expiration=3600,
        content_type="text/plain",
        filename="presigned-test.txt",
        min_size=1,
        max_size=1024 * 1024,  # 1MB
    )


@pytest.fixture
def presigned_download_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.PRESIGNED_DOWNLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key="presigned-test-key",
        expiration=3600,
        content_type="text/plain",
        filename="presigned-test.txt",
    )


@pytest.fixture
def info_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.INFO,
        bucket=_BUCKET_FIXTURE_NAME,
        key="test-key",
        expiration=3600,
    )


@pytest.fixture
def delete_token_data():
    return ObjectStorageTokenData(
        op=ObjectStorageOperationType.DELETE,
        bucket=_BUCKET_FIXTURE_NAME,
        key="test-key",
        expiration=3600,
    )


@pytest.mark.asyncio
async def test_stream_upload_success(s3_client, storages_service, valid_token_data):
    """Test successful stream upload"""

    async def mock_data_stream():
        yield b"chunk 1"
        yield b"chunk 2"

    result = await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, valid_token_data, mock_data_stream()
    )

    assert isinstance(result, UploadResponse)
    assert result.success is True
    assert result.key == "test-key"


@pytest.mark.asyncio
async def test_stream_upload_invalid_storage(storages_service, valid_token_data):
    """Test stream upload with invalid storage name"""

    async def mock_data_stream():
        yield b"test data"

    with pytest.raises(StorageProxyError, match="Upload failed"):
        await storages_service.stream_upload(
            "invalid_storage", _BUCKET_FIXTURE_NAME, valid_token_data, mock_data_stream()
        )


@pytest.mark.asyncio
async def test_stream_upload_invalid_bucket(storages_service, valid_token_data):
    """Test stream upload with invalid bucket name"""

    async def mock_data_stream():
        yield b"test data"

    with pytest.raises(StorageProxyError, match="Upload failed"):
        await storages_service.stream_upload(
            "test_storage", "invalid-bucket", valid_token_data, mock_data_stream()
        )


@pytest.mark.asyncio
async def test_stream_download_success(
    s3_client, storages_service, valid_token_data, download_token_data
):
    """Test successful stream download after upload"""

    # First upload a test file
    async def upload_stream():
        yield b"test chunk 1"
        yield b"test chunk 2"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, valid_token_data, upload_stream()
    )

    # Now download it
    chunks = []
    async for chunk in storages_service.stream_download(
        "test_storage", _BUCKET_FIXTURE_NAME, download_token_data
    ):
        chunks.append(chunk)

    assert len(chunks) >= 1
    combined_data = b"".join(chunks)
    assert b"test chunk 1" in combined_data
    assert b"test chunk 2" in combined_data


@pytest.mark.asyncio
async def test_stream_download_nonexistent_file(s3_client, storages_service, download_token_data):
    """Test stream download of nonexistent file"""
    download_token_data.key = "nonexistent-key"

    with pytest.raises(StorageProxyError, match="Download failed"):
        async for chunk in storages_service.stream_download(
            "test_storage", _BUCKET_FIXTURE_NAME, download_token_data
        ):
            pass


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_success(
    s3_client, storages_service, presigned_upload_token_data
):
    """Test successful presigned upload URL generation and actual upload"""
    import aiohttp

    # Generate presigned upload URL
    result = await storages_service.generate_presigned_upload_url(
        "test_storage", _BUCKET_FIXTURE_NAME, presigned_upload_token_data
    )

    assert isinstance(result, PresignedUploadResponse)
    assert result.url is not None
    assert result.fields is not None
    assert isinstance(result.fields, dict)

    # Test actual upload using the presigned URL
    test_data = b"test file content for presigned upload"

    # Prepare form data for multipart upload
    data = aiohttp.FormData()
    for key, value in result.fields.items():
        data.add_field(key, value)
    data.add_field("file", test_data, filename="test-presigned-file.txt")

    # Perform actual upload
    async with aiohttp.ClientSession() as session:
        async with session.post(result.url, data=data) as upload_response:
            assert upload_response.status in (200, 204), (
                f"Upload failed with status {upload_response.status}"
            )

    # Verify the file was uploaded by downloading it back
    chunks = []
    download_token_data = ObjectStorageTokenData(
        op=ObjectStorageOperationType.DOWNLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key=presigned_upload_token_data.key,
        expiration=3600,
    )

    async for chunk in storages_service.stream_download(
        "test_storage", _BUCKET_FIXTURE_NAME, download_token_data
    ):
        chunks.append(chunk)

    downloaded_data = b"".join(chunks)
    assert downloaded_data == test_data


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_invalid_storage(
    storages_service, presigned_upload_token_data
):
    """Test presigned upload URL generation with invalid storage"""
    with pytest.raises(PresignedUploadURLGenerationError):
        await storages_service.generate_presigned_upload_url(
            "invalid_storage", _BUCKET_FIXTURE_NAME, presigned_upload_token_data
        )


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_invalid_bucket(
    storages_service, presigned_upload_token_data
):
    """Test presigned upload URL generation with invalid bucket"""
    with pytest.raises(PresignedUploadURLGenerationError):
        await storages_service.generate_presigned_upload_url(
            "test_storage", "invalid-bucket", presigned_upload_token_data
        )


@pytest.mark.asyncio
async def test_generate_presigned_download_url_success(
    s3_client, storages_service, valid_token_data, presigned_download_token_data
):
    """Test successful presigned download URL generation and actual download"""
    import aiohttp

    # Use the same key as presigned_download_token_data to avoid key mismatch
    test_data = b"test data for presigned download verification"

    # Upload using the same key that will be used for presigned download
    upload_token_data = ObjectStorageTokenData(
        op=ObjectStorageOperationType.UPLOAD,
        bucket=_BUCKET_FIXTURE_NAME,
        key=presigned_download_token_data.key,  # Use the same key
        expiration=3600,
        content_type="text/plain",
    )

    async def upload_stream():
        yield test_data

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, upload_token_data, upload_stream()
    )

    # Generate presigned download URL
    result = await storages_service.generate_presigned_download_url(
        "test_storage", _BUCKET_FIXTURE_NAME, presigned_download_token_data
    )

    assert isinstance(result, PresignedDownloadResponse)
    assert result.url is not None
    assert result.url.startswith("http")

    # Test actual download using the presigned URL
    async with aiohttp.ClientSession() as session:
        async with session.get(result.url) as download_response:
            assert download_response.status == 200, (
                f"Download failed with status {download_response.status}"
            )
            downloaded_data = await download_response.read()
            assert downloaded_data == test_data, "Downloaded data doesn't match uploaded data"


@pytest.mark.asyncio
async def test_generate_presigned_download_url_invalid_storage(
    storages_service, presigned_download_token_data
):
    """Test presigned download URL generation with invalid storage"""
    with pytest.raises(PresignedDownloadURLGenerationError):
        await storages_service.generate_presigned_download_url(
            "invalid_storage", _BUCKET_FIXTURE_NAME, presigned_download_token_data
        )


@pytest.mark.asyncio
async def test_generate_presigned_download_url_invalid_bucket(
    storages_service, presigned_download_token_data
):
    """Test presigned download URL generation with invalid bucket"""
    with pytest.raises(PresignedDownloadURLGenerationError):
        await storages_service.generate_presigned_download_url(
            "test_storage", "invalid-bucket", presigned_download_token_data
        )


@pytest.mark.asyncio
async def test_get_object_info_success(
    s3_client, storages_service, valid_token_data, info_token_data
):
    """Test successful object info retrieval"""

    # First upload a test file
    async def upload_stream():
        yield b"test data for object info"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, valid_token_data, upload_stream()
    )

    # Get object info
    result = await storages_service.get_object_info(
        "test_storage", _BUCKET_FIXTURE_NAME, info_token_data
    )

    assert isinstance(result, ObjectInfoResponse)
    assert result.content_length is not None
    assert result.content_length > 0
    assert result.content_type is not None
    assert result.etag is not None
    assert result.last_modified is not None


@pytest.mark.asyncio
async def test_get_object_info_nonexistent_file(s3_client, storages_service, info_token_data):
    """Test object info retrieval for nonexistent file"""
    info_token_data.key = "nonexistent-key"

    with pytest.raises(StorageBucketFileNotFoundError):
        await storages_service.get_object_info(
            "test_storage", _BUCKET_FIXTURE_NAME, info_token_data
        )


@pytest.mark.asyncio
async def test_get_object_info_invalid_storage(storages_service, info_token_data):
    """Test object info retrieval with invalid storage"""
    with pytest.raises(StorageProxyError, match="Get object info failed"):
        await storages_service.get_object_info(
            "invalid_storage", _BUCKET_FIXTURE_NAME, info_token_data
        )


@pytest.mark.asyncio
async def test_get_object_info_invalid_bucket(storages_service, info_token_data):
    """Test object info retrieval with invalid bucket"""
    with pytest.raises(StorageProxyError, match="Get object info failed"):
        await storages_service.get_object_info("test_storage", "invalid-bucket", info_token_data)


@pytest.mark.asyncio
async def test_delete_object_success(
    s3_client, storages_service, valid_token_data, delete_token_data
):
    """Test successful object deletion"""

    # First upload a test file
    async def upload_stream():
        yield b"test data for deletion"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, valid_token_data, upload_stream()
    )

    # Delete the object
    result = await storages_service.delete_object(
        "test_storage", _BUCKET_FIXTURE_NAME, delete_token_data
    )

    assert isinstance(result, DeleteResponse)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_object_nonexistent_file(s3_client, storages_service, delete_token_data):
    """Test deletion of nonexistent file (should still return success)"""
    delete_token_data.key = "nonexistent-key"

    result = await storages_service.delete_object(
        "test_storage", _BUCKET_FIXTURE_NAME, delete_token_data
    )

    assert isinstance(result, DeleteResponse)
    # S3 delete operations typically succeed even for nonexistent objects
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_object_invalid_storage(storages_service, delete_token_data):
    """Test object deletion with invalid storage"""
    result = await storages_service.delete_object(
        "invalid_storage", _BUCKET_FIXTURE_NAME, delete_token_data
    )
    # Delete should return failure for invalid storage
    assert isinstance(result, DeleteResponse)
    assert result.success is False


@pytest.mark.asyncio
async def test_delete_object_invalid_bucket(storages_service, delete_token_data):
    """Test object deletion with invalid bucket"""
    result = await storages_service.delete_object(
        "test_storage", "invalid-bucket", delete_token_data
    )
    # Delete should return failure for invalid bucket
    assert isinstance(result, DeleteResponse)
    assert result.success is False


def test_get_s3_client_no_storage_config(storages_service):
    """Test S3 client creation with nonexistent storage config"""
    with pytest.raises(StorageNotFoundError):
        storages_service._get_s3_client("nonexistent-storage", _BUCKET_FIXTURE_NAME)


def test_get_s3_client_invalid_bucket(storages_service):
    """Test S3 client creation with invalid bucket"""
    with pytest.raises(StorageBucketNotFoundError):
        storages_service._get_s3_client("test_storage", "invalid-bucket")
