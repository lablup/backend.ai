"""Tests for ai.backend.common.dto.manager.v2.image.types module."""

from __future__ import annotations

import json
from decimal import Decimal

from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageOrderField,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
    OrderDirection,
)


class TestImageStatusType:
    """Tests for ImageStatusType enum."""

    def test_alive_value(self) -> None:
        assert ImageStatusType.ALIVE.value == "ALIVE"

    def test_deleted_value(self) -> None:
        assert ImageStatusType.DELETED.value == "DELETED"

    def test_all_values_are_strings(self) -> None:
        for member in ImageStatusType:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        assert len(list(ImageStatusType)) == 2

    def test_from_string_alive(self) -> None:
        assert ImageStatusType("ALIVE") is ImageStatusType.ALIVE

    def test_from_string_deleted(self) -> None:
        assert ImageStatusType("DELETED") is ImageStatusType.DELETED


class TestImageTypeEnum:
    """Tests for ImageTypeEnum enum."""

    def test_compute_value(self) -> None:
        assert ImageTypeEnum.COMPUTE.value == "compute"

    def test_system_value(self) -> None:
        assert ImageTypeEnum.SYSTEM.value == "system"

    def test_service_value(self) -> None:
        assert ImageTypeEnum.SERVICE.value == "service"

    def test_enum_members_count(self) -> None:
        assert len(list(ImageTypeEnum)) == 3

    def test_from_string_compute(self) -> None:
        assert ImageTypeEnum("compute") is ImageTypeEnum.COMPUTE

    def test_from_string_system(self) -> None:
        assert ImageTypeEnum("system") is ImageTypeEnum.SYSTEM

    def test_from_string_service(self) -> None:
        assert ImageTypeEnum("service") is ImageTypeEnum.SERVICE


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestImageOrderField:
    """Tests for ImageOrderField enum."""

    def test_name_value(self) -> None:
        assert ImageOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert ImageOrderField.CREATED_AT.value == "created_at"

    def test_last_used_value(self) -> None:
        assert ImageOrderField.LAST_USED.value == "last_used"

    def test_enum_members_count(self) -> None:
        assert len(list(ImageOrderField)) == 3

    def test_from_string_name(self) -> None:
        assert ImageOrderField("name") is ImageOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert ImageOrderField("created_at") is ImageOrderField.CREATED_AT

    def test_from_string_last_used(self) -> None:
        assert ImageOrderField("last_used") is ImageOrderField.LAST_USED


class TestImageTagInfo:
    """Tests for ImageTagInfo Pydantic model."""

    def test_basic_creation(self) -> None:
        tag = ImageTagInfo(key="version", value="1.0")
        assert tag.key == "version"
        assert tag.value == "1.0"

    def test_serialization_round_trip(self) -> None:
        tag = ImageTagInfo(key="env", value="prod")
        json_str = tag.model_dump_json()
        restored = ImageTagInfo.model_validate_json(json_str)
        assert restored.key == tag.key
        assert restored.value == tag.value

    def test_model_dump_json(self) -> None:
        tag = ImageTagInfo(key="k", value="v")
        parsed = json.loads(tag.model_dump_json())
        assert parsed["key"] == "k"
        assert parsed["value"] == "v"


class TestImageLabelInfo:
    """Tests for ImageLabelInfo Pydantic model."""

    def test_basic_creation(self) -> None:
        label = ImageLabelInfo(key="maintainer", value="team@example.com")
        assert label.key == "maintainer"
        assert label.value == "team@example.com"

    def test_serialization_round_trip(self) -> None:
        label = ImageLabelInfo(key="label-key", value="label-value")
        json_str = label.model_dump_json()
        restored = ImageLabelInfo.model_validate_json(json_str)
        assert restored.key == label.key
        assert restored.value == label.value

    def test_model_dump_json(self) -> None:
        label = ImageLabelInfo(key="k", value="v")
        parsed = json.loads(label.model_dump_json())
        assert parsed["key"] == "k"
        assert parsed["value"] == "v"


class TestImageResourceLimitInfo:
    """Tests for ImageResourceLimitInfo Pydantic model."""

    def test_basic_creation_with_max(self) -> None:
        limit = ImageResourceLimitInfo(key="cpu", min=Decimal("0.1"), max=Decimal("8.0"))
        assert limit.key == "cpu"
        assert limit.min == Decimal("0.1")
        assert limit.max == Decimal("8.0")

    def test_creation_with_null_max(self) -> None:
        limit = ImageResourceLimitInfo(key="mem", min=Decimal("256"), max=None)
        assert limit.key == "mem"
        assert limit.min == Decimal("256")
        assert limit.max is None

    def test_serialization_round_trip_with_max(self) -> None:
        limit = ImageResourceLimitInfo(key="gpu", min=Decimal("1"), max=Decimal("4"))
        json_str = limit.model_dump_json()
        restored = ImageResourceLimitInfo.model_validate_json(json_str)
        assert restored.key == limit.key
        assert restored.min == limit.min
        assert restored.max == limit.max

    def test_serialization_round_trip_null_max(self) -> None:
        limit = ImageResourceLimitInfo(key="gpu", min=Decimal("0"), max=None)
        json_str = limit.model_dump_json()
        restored = ImageResourceLimitInfo.model_validate_json(json_str)
        assert restored.key == limit.key
        assert restored.min == limit.min
        assert restored.max is None

    def test_decimal_precision_preserved(self) -> None:
        limit = ImageResourceLimitInfo(key="mem", min=Decimal("0.5"), max=Decimal("16.25"))
        json_str = limit.model_dump_json()
        restored = ImageResourceLimitInfo.model_validate_json(json_str)
        assert restored.min == Decimal("0.5")
        assert restored.max == Decimal("16.25")
