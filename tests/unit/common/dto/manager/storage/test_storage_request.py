"""Tests for storage domain request DTOs."""

import uuid

from ai.backend.common.dto.manager.storage.request import (
    CreateObjectStorageReq,
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    ObjectStoragePathParam,
    UpdateObjectStorageReq,
    VFSDownloadFileReq,
    VFSListFilesReq,
    VFSStoragePathParam,
)


class TestObjectStorageRequestModels:
    def test_create_object_storage_req(self) -> None:
        model = CreateObjectStorageReq(
            name="my-storage",
            host="s3.amazonaws.com",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            endpoint="https://s3.amazonaws.com",
            region="us-east-1",
        )
        assert model.name == "my-storage"
        assert model.host == "s3.amazonaws.com"
        assert model.region == "us-east-1"

    def test_object_storage_path_param(self) -> None:
        uid = uuid.uuid4()
        model = ObjectStoragePathParam(storage_id=uid)
        assert model.storage_id == uid

    def test_update_object_storage_req_partial(self) -> None:
        model = UpdateObjectStorageReq(name="new-name")
        assert model.name == "new-name"
        assert model.host is None
        assert model.access_key is None

    def test_update_object_storage_req_full(self) -> None:
        model = UpdateObjectStorageReq(
            name="updated-storage",
            host="new-host.example.com",
            access_key="new-key",
            secret_key="new-secret",
            endpoint="https://new-endpoint.com",
            region="eu-west-1",
        )
        assert model.name == "updated-storage"
        assert model.region == "eu-west-1"

    def test_create_object_storage_serialization(self) -> None:
        model = CreateObjectStorageReq(
            name="my-storage",
            host="s3.amazonaws.com",
            access_key="key",
            secret_key="secret",
            endpoint="https://s3.amazonaws.com",
            region="us-east-1",
        )
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = CreateObjectStorageReq.model_validate_json(json_data)
        assert restored.name == model.name


class TestPresignedURLRequestModels:
    def test_get_presigned_download_url_req(self) -> None:
        uid = uuid.uuid4()
        model = GetPresignedDownloadURLReq(
            artifact_revision_id=uid,
            key="path/to/file.txt",
        )
        assert model.artifact_revision_id == uid
        assert model.key == "path/to/file.txt"
        assert model.expiration is None

    def test_get_presigned_download_url_req_with_expiration(self) -> None:
        uid = uuid.uuid4()
        model = GetPresignedDownloadURLReq(
            artifact_revision_id=uid,
            key="path/to/file.txt",
            expiration=3600,
        )
        assert model.expiration == 3600

    def test_get_presigned_upload_url_req(self) -> None:
        uid = uuid.uuid4()
        model = GetPresignedUploadURLReq(
            artifact_revision_id=uid,
            key="path/to/file.txt",
        )
        assert model.artifact_revision_id == uid
        assert model.content_type is None
        assert model.min_size is None
        assert model.max_size is None

    def test_get_presigned_upload_url_req_full(self) -> None:
        uid = uuid.uuid4()
        model = GetPresignedUploadURLReq(
            artifact_revision_id=uid,
            key="path/to/file.txt",
            content_type="application/octet-stream",
            expiration=7200,
            min_size=100,
            max_size=1000000,
        )
        assert model.content_type == "application/octet-stream"
        assert model.min_size == 100
        assert model.max_size == 1000000


class TestVFSStorageRequestModels:
    def test_vfs_storage_path_param(self) -> None:
        model = VFSStoragePathParam(storage_name="my-vfs-storage")
        assert model.storage_name == "my-vfs-storage"

    def test_vfs_download_file_req(self) -> None:
        model = VFSDownloadFileReq(filepath="/data/models/model.bin")
        assert model.filepath == "/data/models/model.bin"

    def test_vfs_list_files_req(self) -> None:
        model = VFSListFilesReq(directory="/data/models")
        assert model.directory == "/data/models"

    def test_vfs_storage_path_param_serialization(self) -> None:
        model = VFSStoragePathParam(storage_name="my-vfs-storage")
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = VFSStoragePathParam.model_validate_json(json_data)
        assert restored.storage_name == model.storage_name

    def test_vfs_download_file_req_serialization(self) -> None:
        model = VFSDownloadFileReq(filepath="/data/file.txt")
        json_data = model.model_dump_json()
        restored = VFSDownloadFileReq.model_validate_json(json_data)
        assert restored.filepath == model.filepath

    def test_vfs_list_files_req_serialization(self) -> None:
        model = VFSListFilesReq(directory="/data")
        json_data = model.model_dump_json()
        restored = VFSListFilesReq.model_validate_json(json_data)
        assert restored.directory == model.directory
