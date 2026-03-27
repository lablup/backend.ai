"""Tests for storage domain response DTOs."""

import uuid

from ai.backend.common.dto.manager.storage.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    GetVFSStorageResponse,
    ListVFSStorageResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
    ObjectStorageResponse,
    VFSStorage,
)


class TestObjectStorageResponseModels:
    def test_object_storage_response(self) -> None:
        model = ObjectStorageResponse(
            id="storage-123",
            name="my-storage",
            host="s3.amazonaws.com",
            access_key="key",
            secret_key="secret",
            endpoint="https://s3.amazonaws.com",
            region="us-east-1",
        )
        assert model.id == "storage-123"
        assert model.name == "my-storage"
        assert model.region == "us-east-1"

    def test_object_storage_list_response(self) -> None:
        storage = ObjectStorageResponse(
            id="s1",
            name="storage-1",
            host="host1",
            access_key="key1",
            secret_key="secret1",
            endpoint="https://ep1.com",
            region="us-east-1",
        )
        model = ObjectStorageListResponse(storages=[storage])
        assert len(model.storages) == 1
        assert model.storages[0].name == "storage-1"

    def test_object_storage_list_response_empty(self) -> None:
        model = ObjectStorageListResponse(storages=[])
        assert len(model.storages) == 0

    def test_object_storage_response_serialization(self) -> None:
        model = ObjectStorageResponse(
            id="s1",
            name="test",
            host="host",
            access_key="ak",
            secret_key="sk",
            endpoint="ep",
            region="r",
        )
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = ObjectStorageResponse.model_validate_json(json_data)
        assert restored.id == model.id


class TestPresignedURLResponseModels:
    def test_get_presigned_download_url_response(self) -> None:
        model = GetPresignedDownloadURLResponse(
            presigned_url="https://example.com/download?token=abc"
        )
        assert model.presigned_url == "https://example.com/download?token=abc"

    def test_get_presigned_upload_url_response(self) -> None:
        model = GetPresignedUploadURLResponse(
            presigned_url="https://example.com/upload?token=def",
            fields='{"key": "value"}',
        )
        assert model.presigned_url == "https://example.com/upload?token=def"
        assert model.fields == '{"key": "value"}'


class TestObjectStorageBucketModels:
    def test_object_storage_buckets_response(self) -> None:
        model = ObjectStorageBucketsResponse(buckets=["bucket1", "bucket2"])
        assert len(model.buckets) == 2
        assert "bucket1" in model.buckets

    def test_object_storage_all_buckets_response(self) -> None:
        uid1 = uuid.uuid4()
        uid2 = uuid.uuid4()
        model = ObjectStorageAllBucketsResponse(
            buckets_by_storage={
                uid1: ["bucket-a", "bucket-b"],
                uid2: ["bucket-c"],
            }
        )
        assert len(model.buckets_by_storage) == 2
        assert len(model.buckets_by_storage[uid1]) == 2

    def test_object_storage_all_buckets_serialization(self) -> None:
        uid = uuid.uuid4()
        model = ObjectStorageAllBucketsResponse(buckets_by_storage={uid: ["b1", "b2"]})
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = ObjectStorageAllBucketsResponse.model_validate_json(json_data)
        assert uid in restored.buckets_by_storage


class TestVFSStorageResponseModels:
    def test_vfs_storage(self) -> None:
        model = VFSStorage(name="vfs-1", base_path="/mnt/data", host="storage-host")
        assert model.name == "vfs-1"
        assert model.base_path == "/mnt/data"
        assert model.host == "storage-host"

    def test_get_vfs_storage_response(self) -> None:
        storage = VFSStorage(name="vfs-1", base_path="/mnt/data", host="storage-host")
        model = GetVFSStorageResponse(storage=storage)
        assert model.storage.name == "vfs-1"

    def test_list_vfs_storage_response(self) -> None:
        storages = [
            VFSStorage(name="vfs-1", base_path="/mnt/data1", host="host1"),
            VFSStorage(name="vfs-2", base_path="/mnt/data2", host="host2"),
        ]
        model = ListVFSStorageResponse(storages=storages)
        assert len(model.storages) == 2
        assert model.storages[0].name == "vfs-1"
        assert model.storages[1].name == "vfs-2"

    def test_list_vfs_storage_response_empty(self) -> None:
        model = ListVFSStorageResponse(storages=[])
        assert len(model.storages) == 0

    def test_vfs_storage_serialization(self) -> None:
        model = VFSStorage(name="vfs-1", base_path="/mnt/data", host="host")
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = VFSStorage.model_validate_json(json_data)
        assert restored.name == model.name

    def test_get_vfs_storage_response_serialization(self) -> None:
        storage = VFSStorage(name="vfs-1", base_path="/mnt/data", host="host")
        model = GetVFSStorageResponse(storage=storage)
        json_data = model.model_dump_json()
        restored = GetVFSStorageResponse.model_validate_json(json_data)
        assert restored.storage.name == model.storage.name
