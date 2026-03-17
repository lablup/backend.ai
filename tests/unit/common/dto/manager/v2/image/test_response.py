"""Tests for ai.backend.common.dto.manager.v2.image.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.image.response import (
    AliasImagePayload,
    ForgetImagePayload,
    GetImagePayload,
    ImageNode,
    PurgeImagePayload,
    RescanImagesPayload,
    SearchImagesPayload,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
)


def make_image_node(**kwargs: object) -> ImageNode:
    """Helper to create a minimal valid ImageNode."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "python:3.11-cuda12",
        "registry": "registry.example.com",
        "registry_id": uuid.uuid4(),
        "architecture": "x86_64",
        "size_bytes": 1024 * 1024 * 500,
        "type": ImageTypeEnum.COMPUTE,
        "status": ImageStatusType.ALIVE,
        "config_digest": "sha256:abc123",
        "is_local": False,
    }
    defaults.update(kwargs)
    return ImageNode(**defaults)  # type: ignore[arg-type]


class TestImageNodeCreation:
    """Tests for ImageNode model creation."""

    def test_creation_with_minimal_fields(self) -> None:
        node = make_image_node()
        assert node.project is None
        assert node.tag is None
        assert node.labels == []
        assert node.tags == []
        assert node.resource_limits == []
        assert node.accelerators is None
        assert node.created_at is None

    def test_creation_with_all_fields(self) -> None:
        image_id = uuid.uuid4()
        registry_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = ImageNode(
            id=image_id,
            name="python:3.11",
            registry="registry.example.com",
            registry_id=registry_id,
            project="myproject",
            tag="latest",
            architecture="x86_64",
            size_bytes=500_000_000,
            type=ImageTypeEnum.COMPUTE,
            status=ImageStatusType.ALIVE,
            labels=[ImageLabelInfo(key="maintainer", value="team")],
            tags=[ImageTagInfo(key="version", value="3.11")],
            resource_limits=[
                ImageResourceLimitInfo(key="cpu", min=Decimal("0.1"), max=Decimal("8.0"))
            ],
            accelerators="cuda>=11",
            config_digest="sha256:abc123",
            is_local=False,
            created_at=now,
        )
        assert node.id == image_id
        assert node.project == "myproject"
        assert node.tag == "latest"
        assert len(node.labels) == 1
        assert len(node.tags) == 1
        assert len(node.resource_limits) == 1
        assert node.accelerators == "cuda>=11"
        assert node.created_at == now

    def test_status_alive(self) -> None:
        node = make_image_node(status=ImageStatusType.ALIVE)
        assert node.status == ImageStatusType.ALIVE

    def test_status_deleted(self) -> None:
        node = make_image_node(status=ImageStatusType.DELETED)
        assert node.status == ImageStatusType.DELETED

    def test_type_compute(self) -> None:
        node = make_image_node(type=ImageTypeEnum.COMPUTE)
        assert node.type == ImageTypeEnum.COMPUTE

    def test_type_system(self) -> None:
        node = make_image_node(type=ImageTypeEnum.SYSTEM)
        assert node.type == ImageTypeEnum.SYSTEM

    def test_type_service(self) -> None:
        node = make_image_node(type=ImageTypeEnum.SERVICE)
        assert node.type == ImageTypeEnum.SERVICE


class TestImageNodeNestedFields:
    """Tests for ImageNode with nested list fields."""

    def test_labels_list_multiple(self) -> None:
        labels = [
            ImageLabelInfo(key="maintainer", value="team"),
            ImageLabelInfo(key="version", value="3.11"),
        ]
        node = make_image_node(labels=labels)
        assert len(node.labels) == 2
        assert node.labels[0].key == "maintainer"
        assert node.labels[1].key == "version"

    def test_tags_list_multiple(self) -> None:
        tags = [
            ImageTagInfo(key="env", value="prod"),
            ImageTagInfo(key="tier", value="backend"),
        ]
        node = make_image_node(tags=tags)
        assert len(node.tags) == 2

    def test_resource_limits_multiple(self) -> None:
        limits = [
            ImageResourceLimitInfo(key="cpu", min=Decimal("0"), max=Decimal("8")),
            ImageResourceLimitInfo(key="mem", min=Decimal("256"), max=None),
        ]
        node = make_image_node(resource_limits=limits)
        assert len(node.resource_limits) == 2
        assert node.resource_limits[0].key == "cpu"
        assert node.resource_limits[1].max is None

    def test_nested_labels_serialize_to_json(self) -> None:
        labels = [ImageLabelInfo(key="k", value="v")]
        node = make_image_node(labels=labels)
        data = json.loads(node.model_dump_json())
        assert isinstance(data["labels"], list)
        assert data["labels"][0]["key"] == "k"
        assert data["labels"][0]["value"] == "v"

    def test_nested_resource_limits_serialize_to_json(self) -> None:
        limits = [ImageResourceLimitInfo(key="cpu", min=Decimal("0.1"), max=Decimal("4"))]
        node = make_image_node(resource_limits=limits)
        data = json.loads(node.model_dump_json())
        assert isinstance(data["resource_limits"], list)
        assert data["resource_limits"][0]["key"] == "cpu"


class TestImageNodeRoundTrip:
    """Tests for ImageNode serialization round-trip."""

    def test_round_trip_minimal_fields(self) -> None:
        node = make_image_node()
        json_str = node.model_dump_json()
        restored = ImageNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.registry == node.registry
        assert restored.architecture == node.architecture
        assert restored.type == node.type
        assert restored.status == node.status

    def test_round_trip_with_nested_lists(self) -> None:
        node = make_image_node(
            labels=[ImageLabelInfo(key="k", value="v")],
            tags=[ImageTagInfo(key="t", value="tv")],
            resource_limits=[
                ImageResourceLimitInfo(key="cpu", min=Decimal("0.5"), max=Decimal("4"))
            ],
        )
        json_str = node.model_dump_json()
        restored = ImageNode.model_validate_json(json_str)
        assert len(restored.labels) == 1
        assert restored.labels[0].key == "k"
        assert len(restored.tags) == 1
        assert restored.tags[0].key == "t"
        assert len(restored.resource_limits) == 1
        assert restored.resource_limits[0].min == Decimal("0.5")

    def test_round_trip_preserves_decimal_precision(self) -> None:
        node = make_image_node(
            resource_limits=[
                ImageResourceLimitInfo(key="mem", min=Decimal("0.25"), max=Decimal("16.75"))
            ]
        )
        json_str = node.model_dump_json()
        restored = ImageNode.model_validate_json(json_str)
        assert restored.resource_limits[0].min == Decimal("0.25")
        assert restored.resource_limits[0].max == Decimal("16.75")


class TestSearchImagesPayload:
    """Tests for SearchImagesPayload model."""

    def test_creation(self) -> None:
        node = make_image_node()
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = SearchImagesPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.pagination.total == 1

    def test_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=50)
        payload = SearchImagesPayload(items=[], pagination=pagination)
        assert payload.items == []

    def test_round_trip_serialization(self) -> None:
        node = make_image_node()
        pagination = PaginationInfo(total=1, offset=0, limit=50)
        payload = SearchImagesPayload(items=[node], pagination=pagination)
        json_str = payload.model_dump_json()
        restored = SearchImagesPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == node.id
        assert restored.pagination.total == 1


class TestGetImagePayload:
    """Tests for GetImagePayload model."""

    def test_creation(self) -> None:
        node = make_image_node()
        payload = GetImagePayload(item=node)
        assert payload.item.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_image_node()
        payload = GetImagePayload(item=node)
        json_str = payload.model_dump_json()
        restored = GetImagePayload.model_validate_json(json_str)
        assert restored.item.id == node.id
        assert restored.item.name == node.name


class TestRescanImagesPayload:
    """Tests for RescanImagesPayload model."""

    def test_creation_no_errors(self) -> None:
        node = make_image_node()
        payload = RescanImagesPayload(item=node)
        assert payload.errors == []

    def test_creation_with_errors(self) -> None:
        node = make_image_node()
        payload = RescanImagesPayload(item=node, errors=["failed to pull", "timeout"])
        assert len(payload.errors) == 2
        assert payload.errors[0] == "failed to pull"

    def test_round_trip_serialization(self) -> None:
        node = make_image_node()
        payload = RescanImagesPayload(item=node, errors=["err1"])
        json_str = payload.model_dump_json()
        restored = RescanImagesPayload.model_validate_json(json_str)
        assert restored.item.id == node.id
        assert restored.errors == ["err1"]


class TestAliasImagePayload:
    """Tests for AliasImagePayload model."""

    def test_creation(self) -> None:
        alias_id = uuid.uuid4()
        image_id = uuid.uuid4()
        payload = AliasImagePayload(alias_id=alias_id, alias="my-alias", image_id=image_id)
        assert payload.alias_id == alias_id
        assert payload.alias == "my-alias"
        assert payload.image_id == image_id

    def test_round_trip_serialization(self) -> None:
        alias_id = uuid.uuid4()
        image_id = uuid.uuid4()
        payload = AliasImagePayload(alias_id=alias_id, alias="test-alias", image_id=image_id)
        json_str = payload.model_dump_json()
        restored = AliasImagePayload.model_validate_json(json_str)
        assert restored.alias_id == alias_id
        assert restored.alias == "test-alias"
        assert restored.image_id == image_id


class TestForgetImagePayload:
    """Tests for ForgetImagePayload model."""

    def test_creation(self) -> None:
        node = make_image_node()
        payload = ForgetImagePayload(item=node)
        assert payload.item.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_image_node()
        payload = ForgetImagePayload(item=node)
        json_str = payload.model_dump_json()
        restored = ForgetImagePayload.model_validate_json(json_str)
        assert restored.item.id == node.id


class TestPurgeImagePayload:
    """Tests for PurgeImagePayload model."""

    def test_creation(self) -> None:
        node = make_image_node()
        payload = PurgeImagePayload(item=node)
        assert payload.item.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = make_image_node()
        payload = PurgeImagePayload(item=node)
        json_str = payload.model_dump_json()
        restored = PurgeImagePayload.model_validate_json(json_str)
        assert restored.item.id == node.id
