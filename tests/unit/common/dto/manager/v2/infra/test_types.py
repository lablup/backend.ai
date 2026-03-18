"""Tests for ai.backend.common.dto.manager.v2.infra.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.infra.types import (
    AcceleratorMetadataInfo,
    InfraOrderField,
    NumberFormatInfo,
    OrderDirection,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestInfraOrderField:
    """Tests for InfraOrderField enum."""

    def test_name_value(self) -> None:
        assert InfraOrderField.NAME.value == "name"

    def test_all_values_are_strings(self) -> None:
        for member in InfraOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert InfraOrderField("name") is InfraOrderField.NAME


class TestNumberFormatInfo:
    """Tests for NumberFormatInfo model creation and serialization."""

    def test_creation_binary_true(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=2)
        assert info.binary is True
        assert info.round_length == 2

    def test_creation_binary_false(self) -> None:
        info = NumberFormatInfo(binary=False, round_length=0)
        assert info.binary is False
        assert info.round_length == 0

    def test_round_trip_preserves_fields(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=3)
        json_str = info.model_dump_json()
        restored = NumberFormatInfo.model_validate_json(json_str)
        assert restored.binary == info.binary
        assert restored.round_length == info.round_length

    def test_json_has_expected_keys(self) -> None:
        info = NumberFormatInfo(binary=False, round_length=1)
        parsed = json.loads(info.model_dump_json())
        assert set(parsed.keys()) == {"binary", "round_length"}


class TestAcceleratorMetadataInfo:
    """Tests for AcceleratorMetadataInfo model creation and serialization."""

    def _make_info(self) -> AcceleratorMetadataInfo:
        number_format = NumberFormatInfo(binary=False, round_length=0)
        return AcceleratorMetadataInfo(
            slot_name="cuda.device",
            description="CUDA GPU device",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=number_format,
            display_icon="gpu",
        )

    def test_creation_with_all_fields(self) -> None:
        info = self._make_info()
        assert info.slot_name == "cuda.device"
        assert info.description == "CUDA GPU device"
        assert info.human_readable_name == "GPU"
        assert info.display_unit == "GPU"
        assert info.display_icon == "gpu"

    def test_nested_number_format_is_correct_type(self) -> None:
        info = self._make_info()
        assert isinstance(info.number_format, NumberFormatInfo)

    def test_nested_number_format_fields(self) -> None:
        info = self._make_info()
        assert info.number_format.binary is False
        assert info.number_format.round_length == 0

    def test_round_trip_preserves_all_fields(self) -> None:
        info = self._make_info()
        json_str = info.model_dump_json()
        restored = AcceleratorMetadataInfo.model_validate_json(json_str)
        assert restored.slot_name == info.slot_name
        assert restored.description == info.description
        assert restored.human_readable_name == info.human_readable_name
        assert restored.display_unit == info.display_unit
        assert restored.display_icon == info.display_icon

    def test_round_trip_preserves_nested_number_format(self) -> None:
        info = self._make_info()
        json_str = info.model_dump_json()
        restored = AcceleratorMetadataInfo.model_validate_json(json_str)
        assert restored.number_format.binary == info.number_format.binary
        assert restored.number_format.round_length == info.number_format.round_length

    def test_json_has_number_format_nested(self) -> None:
        info = self._make_info()
        parsed = json.loads(info.model_dump_json())
        assert "number_format" in parsed
        assert isinstance(parsed["number_format"], dict)
        assert "binary" in parsed["number_format"]
        assert "round_length" in parsed["number_format"]

    def test_creation_from_dict(self) -> None:
        data = {
            "slot_name": "rocm.device",
            "description": "AMD ROCm GPU",
            "human_readable_name": "ROCm GPU",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "amd-gpu",
        }
        info = AcceleratorMetadataInfo.model_validate(data)
        assert info.slot_name == "rocm.device"
        assert info.number_format.binary is False
