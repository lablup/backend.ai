"""Tests for ai.backend.common.dto.manager.v2.image.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.image.request import (
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    ImageFilter,
    ImageOrder,
    PurgeImageInput,
    RescanImagesInput,
    SearchImagesInput,
)
from ai.backend.common.dto.manager.v2.image.types import ImageOrderField, OrderDirection


class TestSearchImagesInput:
    """Tests for SearchImagesInput model."""

    def test_default_creation(self) -> None:
        req = SearchImagesInput()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_custom_limit_and_offset(self) -> None:
        req = SearchImagesInput(limit=100, offset=20)
        assert req.limit == 100
        assert req.offset == 20

    def test_limit_minimum_valid(self) -> None:
        req = SearchImagesInput(limit=1)
        assert req.limit == 1

    def test_limit_maximum_valid(self) -> None:
        req = SearchImagesInput(limit=1000)
        assert req.limit == 1000

    def test_limit_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchImagesInput(limit=0)

    def test_limit_above_maximum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchImagesInput(limit=1001)

    def test_negative_offset_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchImagesInput(offset=-1)

    def test_offset_zero_is_valid(self) -> None:
        req = SearchImagesInput(offset=0)
        assert req.offset == 0

    def test_with_filter(self) -> None:
        f = ImageFilter(name=StringFilter(equals="python"))
        req = SearchImagesInput(filter=f)
        assert req.filter is not None
        assert req.filter.name is not None

    def test_with_order(self) -> None:
        order = ImageOrder(field=ImageOrderField.NAME, direction=OrderDirection.DESC)
        req = SearchImagesInput(order=[order])
        assert req.order is not None
        assert len(req.order) == 1
        assert req.order[0].field == ImageOrderField.NAME

    def test_round_trip_serialization(self) -> None:
        req = SearchImagesInput(limit=25, offset=50)
        json_str = req.model_dump_json()
        restored = SearchImagesInput.model_validate_json(json_str)
        assert restored.limit == 25
        assert restored.offset == 50


class TestImageFilter:
    """Tests for ImageFilter model."""

    def test_default_creation(self) -> None:
        f = ImageFilter()
        assert f.name is None
        assert f.architecture is None

    def test_with_name_filter(self) -> None:
        f = ImageFilter(name=StringFilter(equals="python"))
        assert f.name is not None

    def test_with_architecture_filter(self) -> None:
        f = ImageFilter(architecture=StringFilter(equals="x86_64"))
        assert f.architecture is not None


class TestImageOrder:
    """Tests for ImageOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = ImageOrder(field=ImageOrderField.NAME)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = ImageOrder(field=ImageOrderField.CREATED_AT, direction=OrderDirection.DESC)
        assert order.direction == OrderDirection.DESC

    def test_all_order_fields(self) -> None:
        for field in ImageOrderField:
            order = ImageOrder(field=field)
            assert order.field == field


class TestRescanImagesInput:
    """Tests for RescanImagesInput model."""

    def test_valid_creation(self) -> None:
        req = RescanImagesInput(canonical="python:3.11", architecture="x86_64")
        assert req.canonical == "python:3.11"
        assert req.architecture == "x86_64"

    def test_empty_canonical_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            RescanImagesInput(canonical="", architecture="x86_64")

    def test_empty_architecture_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            RescanImagesInput(canonical="python:3.11", architecture="")

    def test_round_trip_serialization(self) -> None:
        req = RescanImagesInput(canonical="cuda:12.0", architecture="aarch64")
        json_str = req.model_dump_json()
        restored = RescanImagesInput.model_validate_json(json_str)
        assert restored.canonical == req.canonical
        assert restored.architecture == req.architecture


class TestAliasImageInput:
    """Tests for AliasImageInput model."""

    def test_valid_creation(self) -> None:
        image_id = uuid.uuid4()
        req = AliasImageInput(image_id=image_id, alias="my-alias")
        assert req.image_id == image_id
        assert req.alias == "my-alias"

    def test_alias_whitespace_stripped(self) -> None:
        image_id = uuid.uuid4()
        req = AliasImageInput(image_id=image_id, alias="  my-alias  ")
        assert req.alias == "my-alias"

    def test_whitespace_only_alias_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageInput(image_id=uuid.uuid4(), alias="   ")

    def test_empty_alias_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageInput(image_id=uuid.uuid4(), alias="")

    def test_alias_max_length_valid(self) -> None:
        image_id = uuid.uuid4()
        req = AliasImageInput(image_id=image_id, alias="a" * 256)
        assert len(req.alias) == 256

    def test_alias_exceeds_max_length_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageInput(image_id=uuid.uuid4(), alias="a" * 257)

    def test_invalid_uuid_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            AliasImageInput.model_validate({"image_id": "not-a-uuid", "alias": "alias"})

    def test_round_trip_serialization(self) -> None:
        image_id = uuid.uuid4()
        req = AliasImageInput(image_id=image_id, alias="test-alias")
        json_str = req.model_dump_json()
        restored = AliasImageInput.model_validate_json(json_str)
        assert restored.image_id == image_id
        assert restored.alias == "test-alias"


class TestDealiasImageInput:
    """Tests for DealiasImageInput model."""

    def test_valid_creation(self) -> None:
        req = DealiasImageInput(alias="my-alias")
        assert req.alias == "my-alias"

    def test_empty_alias_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DealiasImageInput(alias="")

    def test_round_trip_serialization(self) -> None:
        req = DealiasImageInput(alias="test-alias")
        json_str = req.model_dump_json()
        restored = DealiasImageInput.model_validate_json(json_str)
        assert restored.alias == req.alias


class TestForgetImageInput:
    """Tests for ForgetImageInput model."""

    def test_valid_creation(self) -> None:
        image_id = uuid.uuid4()
        req = ForgetImageInput(image_id=image_id)
        assert req.image_id == image_id

    def test_valid_from_uuid_string(self) -> None:
        image_id = uuid.uuid4()
        req = ForgetImageInput.model_validate({"image_id": str(image_id)})
        assert req.image_id == image_id

    def test_invalid_uuid_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ForgetImageInput.model_validate({"image_id": "not-a-uuid"})

    def test_missing_id_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ForgetImageInput.model_validate({})

    def test_image_id_is_uuid_instance(self) -> None:
        image_id = uuid.uuid4()
        req = ForgetImageInput(image_id=image_id)
        assert isinstance(req.image_id, uuid.UUID)

    def test_round_trip_serialization(self) -> None:
        image_id = uuid.uuid4()
        req = ForgetImageInput(image_id=image_id)
        json_str = req.model_dump_json()
        restored = ForgetImageInput.model_validate_json(json_str)
        assert restored.image_id == image_id


class TestPurgeImageInput:
    """Tests for PurgeImageInput model."""

    def test_valid_creation(self) -> None:
        image_id = uuid.uuid4()
        req = PurgeImageInput(image_id=image_id)
        assert req.image_id == image_id

    def test_valid_from_uuid_string(self) -> None:
        image_id = uuid.uuid4()
        req = PurgeImageInput.model_validate({"image_id": str(image_id)})
        assert req.image_id == image_id

    def test_invalid_uuid_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            PurgeImageInput.model_validate({"image_id": "not-a-uuid"})

    def test_missing_id_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            PurgeImageInput.model_validate({})

    def test_image_id_is_uuid_instance(self) -> None:
        image_id = uuid.uuid4()
        req = PurgeImageInput(image_id=image_id)
        assert isinstance(req.image_id, uuid.UUID)

    def test_round_trip_serialization(self) -> None:
        image_id = uuid.uuid4()
        req = PurgeImageInput(image_id=image_id)
        json_str = req.model_dump_json()
        restored = PurgeImageInput.model_validate_json(json_str)
        assert restored.image_id == image_id
