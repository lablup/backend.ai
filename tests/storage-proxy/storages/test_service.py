import pytest

from ai.backend.common.dto.storage.response import (
    PresignedUploadObjectResponse,
)
from ai.backend.storage.config.unified import ObjectStorageConfig, ReservoirConfig
from ai.backend.storage.exception import (
    FileStreamDownloadError,
    FileStreamUploadError,
    ObjectInfoFetchError,
    PresignedDownloadURLGenerationError,
    PresignedUploadURLGenerationError,
    StorageBucketNotFoundError,
    StorageNotFoundError,
)
from ai.backend.storage.services.storages.object_storage import ObjectStorageService

_BUCKET_FIXTURE_NAME = "test-bucket"


@pytest.fixture
def storage_config(minio_container) -> ObjectStorageConfig:
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
def storages_service(storage_config) -> ObjectStorageService:
    return ObjectStorageService([storage_config])


@pytest.fixture
def reservoir_config(minio_container) -> ReservoirConfig:
    container_id, host_port = minio_container
    return ReservoirConfig(
        type="reservoir",
        endpoint=f"http://{host_port.host}:{host_port.port}",
        object_storage_access_key="minioadmin",
        object_storage_secret_key="minioadmin",
        object_storage_region="us-east-1",
    )


# Test configuration constants
_TEST_KEY = "test-key"
_TEST_CONTENT_TYPE = "application/octet-stream"
_PRESIGNED_TEST_KEY = "presigned-test-key"


@pytest.mark.asyncio
async def test_stream_upload_success(s3_client, storages_service: ObjectStorageService):
    """Test successful stream upload"""

    async def mock_data_stream():
        yield b"chunk 1"
        yield b"chunk 2"

    await storages_service.stream_upload(
        "test_storage",
        _BUCKET_FIXTURE_NAME,
        _TEST_KEY,
        _TEST_CONTENT_TYPE,
        mock_data_stream(),
    )


@pytest.mark.asyncio
async def test_stream_upload_invalid_storage(storages_service: ObjectStorageService):
    """Test stream upload with invalid storage name"""

    async def mock_data_stream():
        yield b"test data"

    with pytest.raises(FileStreamUploadError):
        await storages_service.stream_upload(
            "invalid_storage",
            _BUCKET_FIXTURE_NAME,
            _TEST_KEY,
            _TEST_CONTENT_TYPE,
            mock_data_stream(),
        )


@pytest.mark.asyncio
async def test_stream_upload_invalid_bucket(storages_service: ObjectStorageService):
    """Test stream upload with invalid bucket name"""

    async def mock_data_stream():
        yield b"test data"

    with pytest.raises(FileStreamUploadError):
        await storages_service.stream_upload(
            "test_storage",
            "invalid-bucket",
            _TEST_KEY,
            _TEST_CONTENT_TYPE,
            mock_data_stream(),
        )


@pytest.mark.asyncio
async def test_stream_download_success(s3_client, storages_service: ObjectStorageService):
    """Test successful stream download after upload"""

    # First upload a test file
    async def upload_stream():
        yield b"test chunk 1"
        yield b"test chunk 2"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, _TEST_CONTENT_TYPE, upload_stream()
    )

    # Now download it
    chunks = []
    async for chunk in storages_service.stream_download(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY
    ):
        chunks.append(chunk)

    assert len(chunks) >= 1
    combined_data = b"".join(chunks)
    assert b"test chunk 1" in combined_data
    assert b"test chunk 2" in combined_data


@pytest.mark.asyncio
async def test_stream_download_nonexistent_file(s3_client, storages_service: ObjectStorageService):
    """Test stream download of nonexistent file"""
    with pytest.raises(FileStreamDownloadError):
        async for chunk in storages_service.stream_download(
            "test_storage", _BUCKET_FIXTURE_NAME, "nonexistent-key"
        ):
            pass


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_success(
    s3_client, storages_service: ObjectStorageService
):
    """Test successful presigned upload URL generation and actual upload"""
    import aiohttp

    # Generate presigned upload URL
    result = await storages_service.generate_presigned_upload_url(
        "test_storage", _BUCKET_FIXTURE_NAME, _PRESIGNED_TEST_KEY
    )

    assert isinstance(result, PresignedUploadObjectResponse)
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
    async for chunk in storages_service.stream_download(
        "test_storage", _BUCKET_FIXTURE_NAME, _PRESIGNED_TEST_KEY
    ):
        chunks.append(chunk)

    downloaded_data = b"".join(chunks)
    assert downloaded_data == test_data


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_invalid_storage(
    storages_service: ObjectStorageService,
):
    """Test presigned upload URL generation with invalid storage"""
    with pytest.raises(PresignedUploadURLGenerationError):
        await storages_service.generate_presigned_upload_url(
            "invalid_storage", _BUCKET_FIXTURE_NAME, _PRESIGNED_TEST_KEY
        )


@pytest.mark.asyncio
async def test_generate_presigned_upload_url_invalid_bucket(storages_service: ObjectStorageService):
    """Test presigned upload URL generation with invalid bucket"""
    with pytest.raises(PresignedUploadURLGenerationError):
        await storages_service.generate_presigned_upload_url(
            "test_storage", "invalid-bucket", _PRESIGNED_TEST_KEY
        )


@pytest.mark.asyncio
async def test_generate_presigned_download_url_success(
    s3_client, storages_service: ObjectStorageService
):
    """Test successful presigned download URL generation and actual download"""
    import aiohttp

    # Use the same key as presigned_download_token_data to avoid key mismatch
    test_data = b"test data for presigned download verification"

    # Upload using the same key that will be used for presigned download
    async def upload_stream():
        yield test_data

    await storages_service.stream_upload(
        "test_storage",
        _BUCKET_FIXTURE_NAME,
        _PRESIGNED_TEST_KEY,
        "text/plain",
        upload_stream(),
    )

    # Generate presigned download URL
    result = await storages_service.generate_presigned_download_url(
        "test_storage", _BUCKET_FIXTURE_NAME, _PRESIGNED_TEST_KEY
    )

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
    storages_service: ObjectStorageService,
):
    """Test presigned download URL generation with invalid storage"""
    with pytest.raises(PresignedDownloadURLGenerationError):
        await storages_service.generate_presigned_download_url(
            "invalid_storage", _BUCKET_FIXTURE_NAME, _PRESIGNED_TEST_KEY
        )


@pytest.mark.asyncio
async def test_generate_presigned_download_url_invalid_bucket(
    storages_service: ObjectStorageService,
):
    """Test presigned download URL generation with invalid bucket"""
    with pytest.raises(PresignedDownloadURLGenerationError):
        await storages_service.generate_presigned_download_url(
            "test_storage", "invalid-bucket", _PRESIGNED_TEST_KEY
        )


@pytest.mark.asyncio
async def test_get_object_info_success(s3_client, storages_service: ObjectStorageService):
    """Test successful object info retrieval"""

    # First upload a test file
    async def upload_stream():
        yield b"test data for object info"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, _TEST_CONTENT_TYPE, upload_stream()
    )

    # Get object info
    result = await storages_service.get_object_info("test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)

    assert result.content_length is not None
    assert result.content_length > 0
    assert result.content_type is not None
    assert result.etag is not None
    assert result.last_modified is not None


@pytest.mark.asyncio
async def test_get_object_info_nonexistent_file(s3_client, storages_service: ObjectStorageService):
    """Test object info retrieval for nonexistent file"""
    with pytest.raises(ObjectInfoFetchError):
        await storages_service.get_object_info(
            "test_storage", _BUCKET_FIXTURE_NAME, "nonexistent-key"
        )


@pytest.mark.asyncio
async def test_get_object_info_invalid_storage(storages_service: ObjectStorageService):
    """Test object info retrieval with invalid storage"""
    with pytest.raises(ObjectInfoFetchError):
        await storages_service.get_object_info("invalid_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)


@pytest.mark.asyncio
async def test_get_object_info_invalid_bucket(storages_service: ObjectStorageService):
    """Test object info retrieval with invalid bucket"""
    with pytest.raises(ObjectInfoFetchError):
        await storages_service.get_object_info("test_storage", "invalid-bucket", _TEST_KEY)


@pytest.mark.asyncio
async def test_delete_object_success(s3_client, storages_service: ObjectStorageService):
    """Test successful object deletion"""

    # First upload a test file
    async def upload_stream():
        yield b"test data for deletion"

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, _TEST_CONTENT_TYPE, upload_stream()
    )

    # Delete the object
    await storages_service.delete_object("test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)


@pytest.mark.asyncio
async def test_delete_object_nonexistent_file(s3_client, storages_service: ObjectStorageService):
    """Test deletion of nonexistent file (should still return success)"""
    await storages_service.delete_object("test_storage", _BUCKET_FIXTURE_NAME, "nonexistent-key")


@pytest.mark.asyncio
async def test_delete_object_invalid_storage(storages_service: ObjectStorageService):
    """Test object deletion with invalid storage"""
    with pytest.raises(StorageBucketNotFoundError):
        await storages_service.delete_object("invalid_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)


@pytest.mark.asyncio
async def test_delete_object_invalid_bucket(storages_service: ObjectStorageService):
    """Test object deletion with invalid bucket"""
    with pytest.raises(StorageBucketNotFoundError):
        await storages_service.delete_object("test_storage", "invalid-bucket", _TEST_KEY)


def test_get_s3_client_no_storage_config(storages_service: ObjectStorageService):
    """Test S3 client creation with nonexistent storage config"""
    with pytest.raises(StorageNotFoundError):
        storages_service._get_s3_client("nonexistent-storage", _BUCKET_FIXTURE_NAME)


def test_get_s3_client_invalid_bucket(storages_service: ObjectStorageService):
    """Test S3 client creation with invalid bucket"""
    with pytest.raises(StorageBucketNotFoundError):
        storages_service._get_s3_client("test_storage", "invalid-bucket")
