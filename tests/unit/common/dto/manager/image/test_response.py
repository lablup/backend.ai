"""Tests for image response DTO serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from ai.backend.common.dto.manager.image.response import (
    AliasImageResponse,
    ForgetImageResponse,
    GetImageResponse,
    ImageDTO,
    ImageLabelEntryDTO,
    ImageResourceLimitDTO,
    ImageTagEntryDTO,
    PaginationInfo,
    PurgeImageResponse,
    RescanImagesResponse,
    SearchImagesResponse,
)


def _sample_image_dto() -> ImageDTO:
    return ImageDTO(
        id=uuid4(),
        name="cr.backend.ai/stable/python:3.11",
        registry="cr.backend.ai",
        registry_id=uuid4(),
        project="stable",
        tag="3.11",
        architecture="x86_64",
        size_bytes=104857600,
        type="COMPUTE",
        status="ALIVE",
        labels=[ImageLabelEntryDTO(key="ai.backend.role", value="compute")],
        tags=[ImageTagEntryDTO(key="runtime", value="python")],
        resource_limits=[
            ImageResourceLimitDTO(key="cpu", min=Decimal("1"), max=Decimal("8")),
        ],
        accelerators="cuda",
        config_digest="sha256:abc123",
        is_local=False,
        created_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC),
    )


class TestImageDTO:
    def test_serialization(self) -> None:
        dto = _sample_image_dto()
        data = dto.model_dump()

        assert data["name"] == "cr.backend.ai/stable/python:3.11"
        assert data["registry"] == "cr.backend.ai"
        assert data["architecture"] == "x86_64"
        assert data["size_bytes"] == 104857600
        assert data["type"] == "COMPUTE"
        assert data["status"] == "ALIVE"
        assert data["is_local"] is False

    def test_labels_serialization(self) -> None:
        dto = _sample_image_dto()
        data = dto.model_dump()

        assert len(data["labels"]) == 1
        assert data["labels"][0]["key"] == "ai.backend.role"
        assert data["labels"][0]["value"] == "compute"

    def test_resource_limits_serialization(self) -> None:
        dto = _sample_image_dto()
        data = dto.model_dump()

        assert len(data["resource_limits"]) == 1
        assert data["resource_limits"][0]["key"] == "cpu"

    def test_optional_fields(self) -> None:
        dto = ImageDTO(
            id=uuid4(),
            name="test",
            registry="localhost",
            registry_id=uuid4(),
            project=None,
            tag=None,
            architecture="x86_64",
            size_bytes=0,
            type="COMPUTE",
            status="ALIVE",
            config_digest="",
            is_local=True,
        )
        assert dto.project is None
        assert dto.tag is None
        assert dto.accelerators is None
        assert dto.created_at is None
        assert dto.labels == []
        assert dto.tags == []
        assert dto.resource_limits == []


class TestSearchImagesResponse:
    def test_serialization(self) -> None:
        resp = SearchImagesResponse(
            items=[_sample_image_dto(), _sample_image_dto()],
            pagination=PaginationInfo(total=100, offset=0, limit=50),
        )
        data = resp.model_dump()

        assert len(data["items"]) == 2
        assert data["pagination"]["total"] == 100
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["limit"] == 50

    def test_empty_items(self) -> None:
        resp = SearchImagesResponse(
            items=[],
            pagination=PaginationInfo(total=0, offset=0, limit=50),
        )
        data = resp.model_dump()

        assert data["items"] == []
        assert data["pagination"]["total"] == 0


class TestGetImageResponse:
    def test_serialization(self) -> None:
        dto = _sample_image_dto()
        resp = GetImageResponse(item=dto)
        data = resp.model_dump()

        assert data["item"]["name"] == "cr.backend.ai/stable/python:3.11"


class TestRescanImagesResponse:
    def test_serialization(self) -> None:
        dto = _sample_image_dto()
        resp = RescanImagesResponse(item=dto, errors=[])
        data = resp.model_dump()

        assert data["item"]["name"] == "cr.backend.ai/stable/python:3.11"
        assert data["errors"] == []

    def test_with_errors(self) -> None:
        dto = _sample_image_dto()
        resp = RescanImagesResponse(
            item=dto,
            errors=["Tag not found", "Registry unreachable"],
        )
        data = resp.model_dump()

        assert len(data["errors"]) == 2


class TestAliasImageResponse:
    def test_serialization(self) -> None:
        alias_id = uuid4()
        image_id = uuid4()
        resp = AliasImageResponse(alias_id=alias_id, alias="python3", image_id=image_id)
        data = resp.model_dump()

        assert data["alias_id"] == alias_id
        assert data["alias"] == "python3"
        assert data["image_id"] == image_id


class TestForgetImageResponse:
    def test_serialization(self) -> None:
        dto = _sample_image_dto()
        resp = ForgetImageResponse(item=dto)
        data = resp.model_dump()

        assert "item" in data


class TestPurgeImageResponse:
    def test_serialization(self) -> None:
        dto = _sample_image_dto()
        resp = PurgeImageResponse(item=dto)
        data = resp.model_dump()

        assert "item" in data


class TestPaginationInfo:
    def test_with_all_fields(self) -> None:
        p = PaginationInfo(total=100, offset=10, limit=50)
        assert p.total == 100
        assert p.offset == 10
        assert p.limit == 50

    def test_limit_optional(self) -> None:
        p = PaginationInfo(total=50, offset=0)
        assert p.limit is None
