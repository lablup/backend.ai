from collections.abc import AsyncIterator
from typing import Optional

import pytest

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.types import StreamReader
from ai.backend.storage.config.unified import ObjectStorageConfig, ReservoirConfig
from ai.backend.storage.errors import (
    FileStreamDownloadError,
    ObjectInfoFetchError,
    ObjectStorageBucketNotFoundError,
    StorageNotFoundError,
)
from ai.backend.storage.services.storages.object_storage import ObjectStorageService
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool

_BUCKET_FIXTURE_NAME = "test-bucket"


class TestStreamReader(StreamReader):
    def __init__(self, data_chunks: list[bytes]):
        self._data_chunks = data_chunks

    async def read(self) -> AsyncIterator[bytes]:
        for chunk in self._data_chunks:
            yield chunk

    def content_type(self) -> Optional[str]:
        return None


@pytest.fixture
def storage_config(minio_container) -> ObjectStorageConfig:
    container_id, host_port = minio_container
    return ObjectStorageConfig(
        buckets=[_BUCKET_FIXTURE_NAME],
        endpoint=f"http://{host_port.host}:{host_port.port}",
        region="us-east-1",
        access_key="minioadmin",
        secret_key="minioadmin",
    )


@pytest.fixture
def storages_service(storage_config) -> ObjectStorageService:
    storage_name = "test_storage"
    storages: dict[str, AbstractStorage] = {
        storage_name: ObjectStorage(storage_name, storage_config)
    }
    storage_pool = StoragePool(storages)
    return ObjectStorageService(storage_pool)


@pytest.fixture
def reservoir_config(minio_container) -> ReservoirConfig:
    container_id, host_port = minio_container
    return ReservoirConfig(
        endpoint=f"http://{host_port.host}:{host_port.port}",
        object_storage_access_key="minioadmin",
        object_storage_secret_key="minioadmin",
        object_storage_region="us-east-1",
    )


# Test configuration constants
_TEST_KEY = "test-key"
_PRESIGNED_TEST_KEY = "presigned-test-key"


@pytest.mark.asyncio
async def test_stream_upload_success(s3_client, storages_service: ObjectStorageService):
    """Test successful stream upload"""

    test_stream = TestStreamReader([b"chunk 1", b"chunk 2"])

    await storages_service.stream_upload(
        "test_storage",
        _BUCKET_FIXTURE_NAME,
        _TEST_KEY,
        test_stream,
    )


@pytest.mark.asyncio
async def test_stream_upload_invalid_storage(storages_service: ObjectStorageService):
    """Test stream upload with invalid storage name"""

    with pytest.raises(StorageNotFoundError):
        await storages_service.stream_upload(
            "invalid_storage",
            _BUCKET_FIXTURE_NAME,
            _TEST_KEY,
            TestStreamReader([b"test data"]),
        )


@pytest.mark.asyncio
async def test_stream_upload_invalid_bucket(storages_service: ObjectStorageService):
    """Test stream upload with invalid bucket name"""

    test_stream = TestStreamReader([b"test data"])

    with pytest.raises(ObjectStorageBucketNotFoundError):
        await storages_service.stream_upload(
            "test_storage",
            "invalid-bucket",
            _TEST_KEY,
            test_stream,
        )


@pytest.mark.asyncio
async def test_stream_download_success(s3_client, storages_service: ObjectStorageService):
    """Test successful stream download after upload"""

    # First upload a test file
    upload_stream = TestStreamReader([b"test chunk 1", b"test chunk 2"])

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, upload_stream
    )

    # Now download it
    chunks = []
    file_stream = await storages_service.stream_download(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY
    )
    async for chunk in file_stream.read():
        chunks.append(chunk)

    assert len(chunks) >= 1
    combined_data = b"".join(chunks)
    assert b"test chunk 1" in combined_data
    assert b"test chunk 2" in combined_data


@pytest.mark.asyncio
async def test_stream_download_nonexistent_file(s3_client, storages_service: ObjectStorageService):
    """Test stream download of nonexistent file"""
    with pytest.raises(FileStreamDownloadError):
        file_stream = await storages_service.stream_download(
            "test_storage", _BUCKET_FIXTURE_NAME, "nonexistent-key"
        )
        async for chunk in file_stream.read():
            pass


@pytest.mark.asyncio
async def test_get_object_info_success(s3_client, storages_service: ObjectStorageService):
    """Test successful object info retrieval"""

    # First upload a test file
    upload_stream = TestStreamReader([b"test data for object info"])

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, upload_stream
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
    with pytest.raises(StorageNotFoundError):
        await storages_service.get_object_info("invalid_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)


@pytest.mark.asyncio
async def test_get_object_info_invalid_bucket(storages_service: ObjectStorageService):
    """Test object info retrieval with invalid bucket"""
    with pytest.raises(ObjectStorageBucketNotFoundError):
        await storages_service.get_object_info("test_storage", "invalid-bucket", _TEST_KEY)


@pytest.mark.asyncio
async def test_delete_object_success(s3_client, storages_service: ObjectStorageService):
    """Test successful object deletion"""

    # First upload a test file
    upload_stream = TestStreamReader([b"test data for deletion"])

    await storages_service.stream_upload(
        "test_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY, upload_stream
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
    with pytest.raises(StorageNotFoundError):
        await storages_service.delete_object("invalid_storage", _BUCKET_FIXTURE_NAME, _TEST_KEY)


@pytest.mark.asyncio
async def test_delete_object_invalid_bucket(storages_service: ObjectStorageService):
    """Test object deletion with invalid bucket"""
    with pytest.raises(ObjectStorageBucketNotFoundError):
        await storages_service.delete_object("test_storage", "invalid-bucket", _TEST_KEY)
