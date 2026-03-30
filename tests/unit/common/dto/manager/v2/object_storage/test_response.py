"""Tests for ai.backend.common.dto.manager.v2.object_storage.response module."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.object_storage.response import (
    BucketsPayload,
    CreateObjectStoragePayload,
    DeleteObjectStoragePayload,
    ObjectStorageNode,
    PresignedDownloadURLPayload,
    PresignedUploadURLPayload,
    UpdateObjectStoragePayload,
)


def _make_node(region: str | None = "us-east-1") -> ObjectStorageNode:
    return ObjectStorageNode(
        id=uuid.uuid4(),
        name="my-storage",
        host="s3.amazonaws.com",
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI",
        endpoint="https://s3.amazonaws.com",
        region=region,
    )


class TestObjectStorageNode:
    """Tests for ObjectStorageNode model."""

    def test_creation_with_all_fields(self) -> None:
        node = _make_node()
        assert node.name == "my-storage"
        assert node.region == "us-east-1"

    def test_creation_with_none_region(self) -> None:
        node = _make_node(region=None)
        assert node.region is None

    def test_region_default_is_none(self) -> None:
        node = ObjectStorageNode(
            id=uuid.uuid4(),
            name="storage",
            host="host",
            access_key="key",
            secret_key="secret",
            endpoint="https://ep.com",
        )
        assert node.region is None

    def test_round_trip(self) -> None:
        node = _make_node()
        restored = ObjectStorageNode.model_validate_json(node.model_dump_json())
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.region == "us-east-1"

    def test_round_trip_with_none_region(self) -> None:
        node = _make_node(region=None)
        restored = ObjectStorageNode.model_validate_json(node.model_dump_json())
        assert restored.region is None


class TestObjectStoragePayloads:
    """Tests for ObjectStorage payload models."""

    def test_create_payload(self) -> None:
        node = _make_node()
        payload = CreateObjectStoragePayload(object_storage=node)
        assert payload.object_storage.name == "my-storage"

    def test_create_payload_round_trip(self) -> None:
        node = _make_node()
        payload = CreateObjectStoragePayload(object_storage=node)
        restored = CreateObjectStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.object_storage.id == node.id
        assert restored.object_storage.region == "us-east-1"

    def test_update_payload(self) -> None:
        node = _make_node()
        payload = UpdateObjectStoragePayload(object_storage=node)
        assert payload.object_storage is not None

    def test_update_payload_round_trip(self) -> None:
        node = _make_node()
        payload = UpdateObjectStoragePayload(object_storage=node)
        restored = UpdateObjectStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.object_storage.name == "my-storage"

    def test_delete_payload(self) -> None:
        oid = uuid.uuid4()
        payload = DeleteObjectStoragePayload(id=oid)
        assert payload.id == oid

    def test_delete_payload_round_trip(self) -> None:
        oid = uuid.uuid4()
        payload = DeleteObjectStoragePayload(id=oid)
        restored = DeleteObjectStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.id == oid


class TestPresignedURLPayloads:
    """Tests for PresignedURLPayload models."""

    def test_upload_url_payload_fields(self) -> None:
        payload = PresignedUploadURLPayload(
            presigned_url="https://s3.example.com/upload",
            fields='{"key": "value"}',
        )
        assert "s3.example.com" in payload.presigned_url
        assert payload.fields == '{"key": "value"}'

    def test_upload_url_payload_round_trip(self) -> None:
        payload = PresignedUploadURLPayload(
            presigned_url="https://s3.example.com/upload",
            fields="{}",
        )
        restored = PresignedUploadURLPayload.model_validate_json(payload.model_dump_json())
        assert restored.presigned_url == payload.presigned_url
        assert restored.fields == payload.fields

    def test_download_url_payload_field(self) -> None:
        payload = PresignedDownloadURLPayload(presigned_url="https://s3.example.com/download")
        assert "s3.example.com" in payload.presigned_url

    def test_download_url_payload_round_trip(self) -> None:
        payload = PresignedDownloadURLPayload(presigned_url="https://s3.example.com/dl")
        restored = PresignedDownloadURLPayload.model_validate_json(payload.model_dump_json())
        assert restored.presigned_url == "https://s3.example.com/dl"


class TestBucketsPayload:
    """Tests for BucketsPayload model."""

    def test_creation(self) -> None:
        payload = BucketsPayload(buckets=["bucket-a", "bucket-b"])
        assert len(payload.buckets) == 2

    def test_empty_buckets(self) -> None:
        payload = BucketsPayload(buckets=[])
        assert payload.buckets == []

    def test_round_trip(self) -> None:
        payload = BucketsPayload(buckets=["b1", "b2", "b3"])
        restored = BucketsPayload.model_validate_json(payload.model_dump_json())
        assert restored.buckets == ["b1", "b2", "b3"]
