"""Tests for ai.backend.common.dto.manager.v2.object_storage.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.object_storage.request import (
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    GetPresignedDownloadURLInput,
    GetPresignedUploadURLInput,
    UpdateObjectStorageInput,
)


class TestCreateObjectStorageInput:
    """Tests for CreateObjectStorageInput model."""

    def test_valid_creation(self) -> None:
        req = CreateObjectStorageInput(
            name="my-storage",
            host="s3.amazonaws.com",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="secret",
            endpoint="https://s3.amazonaws.com",
            region="us-east-1",
        )
        assert req.name == "my-storage"
        assert req.region == "us-east-1"

    def test_name_whitespace_stripped(self) -> None:
        req = CreateObjectStorageInput(
            name="  my-storage  ",
            host="host",
            access_key="key",
            secret_key="secret",
            endpoint="https://ep.com",
            region="us-west-2",
        )
        assert req.name == "my-storage"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateObjectStorageInput(
                name="",
                host="host",
                access_key="key",
                secret_key="secret",
                endpoint="https://ep.com",
                region="us-east-1",
            )

    def test_whitespace_only_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateObjectStorageInput(
                name="   ",
                host="host",
                access_key="key",
                secret_key="secret",
                endpoint="https://ep.com",
                region="us-east-1",
            )

    def test_name_exceeding_max_length_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateObjectStorageInput(
                name="a" * 257,
                host="host",
                access_key="key",
                secret_key="secret",
                endpoint="https://ep.com",
                region="us-east-1",
            )

    def test_name_at_max_length_is_valid(self) -> None:
        req = CreateObjectStorageInput(
            name="a" * 256,
            host="host",
            access_key="key",
            secret_key="secret",
            endpoint="https://ep.com",
            region="us-east-1",
        )
        assert len(req.name) == 256

    def test_round_trip(self) -> None:
        req = CreateObjectStorageInput(
            name="storage",
            host="host",
            access_key="key",
            secret_key="secret",
            endpoint="https://ep.com",
            region="ap-northeast-2",
        )
        restored = CreateObjectStorageInput.model_validate_json(req.model_dump_json())
        assert restored.name == "storage"
        assert restored.region == "ap-northeast-2"


class TestUpdateObjectStorageInput:
    """Tests for UpdateObjectStorageInput model."""

    def test_default_region_is_sentinel(self) -> None:
        req = UpdateObjectStorageInput()
        assert req.region is SENTINEL
        assert isinstance(req.region, Sentinel)

    def test_region_none_clears_field(self) -> None:
        req = UpdateObjectStorageInput(region=None)
        assert req.region is None

    def test_region_string_updates_field(self) -> None:
        req = UpdateObjectStorageInput(region="eu-west-1")
        assert req.region == "eu-west-1"

    def test_all_none_fields_valid(self) -> None:
        req = UpdateObjectStorageInput(
            name=None, host=None, access_key=None, secret_key=None, endpoint=None, region=None
        )
        assert req.name is None
        assert req.host is None

    def test_partial_update_name_only(self) -> None:
        req = UpdateObjectStorageInput(name="new-name")
        assert req.name == "new-name"
        assert req.host is None


class TestDeleteObjectStorageInput:
    """Tests for DeleteObjectStorageInput model."""

    def test_valid_creation(self) -> None:
        oid = uuid.uuid4()
        req = DeleteObjectStorageInput(id=oid)
        assert req.id == oid

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteObjectStorageInput.model_validate({"id": "not-a-uuid"})

    def test_round_trip(self) -> None:
        oid = uuid.uuid4()
        req = DeleteObjectStorageInput(id=oid)
        restored = DeleteObjectStorageInput.model_validate_json(req.model_dump_json())
        assert restored.id == oid


class TestPresignedURLInputs:
    """Tests for GetPresignedUploadURLInput and GetPresignedDownloadURLInput."""

    def test_upload_url_valid(self) -> None:
        req = GetPresignedUploadURLInput(
            artifact_revision_id=uuid.uuid4(),
            key="path/to/object.bin",
        )
        assert req.key == "path/to/object.bin"
        assert req.content_type is None
        assert req.expiration is None
        assert req.min_size is None
        assert req.max_size is None

    def test_upload_url_with_all_fields(self) -> None:
        req = GetPresignedUploadURLInput(
            artifact_revision_id=uuid.uuid4(),
            key="object.bin",
            content_type="application/octet-stream",
            expiration=3600,
            min_size=0,
            max_size=10485760,
        )
        assert req.expiration == 3600
        assert req.max_size == 10485760

    def test_upload_url_expiration_ge_1(self) -> None:
        with pytest.raises(ValidationError):
            GetPresignedUploadURLInput(
                artifact_revision_id=uuid.uuid4(),
                key="obj",
                expiration=0,
            )

    def test_upload_url_min_size_ge_0(self) -> None:
        with pytest.raises(ValidationError):
            GetPresignedUploadURLInput(
                artifact_revision_id=uuid.uuid4(),
                key="obj",
                min_size=-1,
            )

    def test_download_url_valid(self) -> None:
        req = GetPresignedDownloadURLInput(
            artifact_revision_id=uuid.uuid4(),
            key="path/to/file",
        )
        assert req.expiration is None

    def test_download_url_with_expiration(self) -> None:
        req = GetPresignedDownloadURLInput(
            artifact_revision_id=uuid.uuid4(),
            key="file",
            expiration=7200,
        )
        assert req.expiration == 7200
