"""Tests for image request DTO validation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.image.request import (
    AliasImageRequest,
    DealiasImageRequest,
    ForgetImageRequest,
    ImageFilter,
    ImageOrder,
    PurgeImageRequest,
    RescanImagesRequest,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.types import ImageOrderField, OrderDirection
from ai.backend.common.dto.manager.query import StringFilter


class TestSearchImagesRequest:
    def test_defaults(self) -> None:
        req = SearchImagesRequest()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_custom_pagination(self) -> None:
        req = SearchImagesRequest(limit=100, offset=25)
        assert req.limit == 100
        assert req.offset == 25

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            SearchImagesRequest(limit=0)
        with pytest.raises(ValidationError):
            SearchImagesRequest(limit=1001)

    def test_offset_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            SearchImagesRequest(offset=-1)

    def test_with_filter(self) -> None:
        req = SearchImagesRequest(
            filter=ImageFilter(
                name=StringFilter(contains="python"),
                architecture=StringFilter(equals="x86_64"),
            )
        )
        assert req.filter is not None
        assert req.filter.name is not None
        assert req.filter.name.contains == "python"
        assert req.filter.architecture is not None
        assert req.filter.architecture.equals == "x86_64"

    def test_with_order(self) -> None:
        req = SearchImagesRequest(
            order=[
                ImageOrder(field=ImageOrderField.NAME, direction=OrderDirection.ASC),
                ImageOrder(field=ImageOrderField.CREATED_AT, direction=OrderDirection.DESC),
            ]
        )
        assert req.order is not None
        assert len(req.order) == 2
        assert req.order[0].field == ImageOrderField.NAME
        assert req.order[1].direction == OrderDirection.DESC

    def test_empty_filter(self) -> None:
        req = SearchImagesRequest(filter=ImageFilter())
        assert req.filter is not None
        assert req.filter.name is None
        assert req.filter.architecture is None


class TestRescanImagesRequest:
    def test_valid(self) -> None:
        req = RescanImagesRequest(
            canonical="cr.backend.ai/stable/python:3.11",
            architecture="x86_64",
        )
        assert req.canonical == "cr.backend.ai/stable/python:3.11"
        assert req.architecture == "x86_64"

    def test_missing_canonical(self) -> None:
        with pytest.raises(ValidationError):
            RescanImagesRequest.model_validate({"architecture": "x86_64"})

    def test_missing_architecture(self) -> None:
        with pytest.raises(ValidationError):
            RescanImagesRequest.model_validate({"canonical": "cr.backend.ai/stable/python:3.11"})


class TestAliasImageRequest:
    def test_valid(self) -> None:
        image_id = uuid4()
        req = AliasImageRequest(image_id=image_id, alias="python3")
        assert req.image_id == image_id
        assert req.alias == "python3"

    def test_missing_image_id(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageRequest.model_validate({"alias": "python3"})

    def test_missing_alias(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageRequest.model_validate({"image_id": str(uuid4())})


class TestDealiasImageRequest:
    def test_valid(self) -> None:
        req = DealiasImageRequest(alias="python3")
        assert req.alias == "python3"

    def test_missing_alias(self) -> None:
        with pytest.raises(ValidationError):
            DealiasImageRequest.model_validate({})


class TestForgetImageRequest:
    def test_valid(self) -> None:
        image_id = uuid4()
        req = ForgetImageRequest(image_id=image_id)
        assert req.image_id == image_id

    def test_missing_image_id(self) -> None:
        with pytest.raises(ValidationError):
            ForgetImageRequest.model_validate({})


class TestPurgeImageRequest:
    def test_valid(self) -> None:
        image_id = uuid4()
        req = PurgeImageRequest(image_id=image_id)
        assert req.image_id == image_id

    def test_missing_image_id(self) -> None:
        with pytest.raises(ValidationError):
            PurgeImageRequest.model_validate({})
