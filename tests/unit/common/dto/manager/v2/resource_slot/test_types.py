"""Tests for ai.backend.common.dto.manager.v2.resource_slot.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_slot.types import (
    NumberFormatInfo,
    OrderDirection,
    ResourceSlotTypeOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_present(self) -> None:
        values = {e.value for e in OrderDirection}
        assert values == {"ASC", "DESC"}


class TestResourceSlotTypeOrderField:
    """Tests for ResourceSlotTypeOrderField enum."""

    def test_slot_name_value(self) -> None:
        assert ResourceSlotTypeOrderField.SLOT_NAME.value == "slot_name"

    def test_rank_value(self) -> None:
        assert ResourceSlotTypeOrderField.RANK.value == "rank"

    def test_display_name_value(self) -> None:
        assert ResourceSlotTypeOrderField.DISPLAY_NAME.value == "display_name"

    def test_all_values_present(self) -> None:
        values = {e.value for e in ResourceSlotTypeOrderField}
        assert values == {"slot_name", "rank", "display_name"}


class TestNumberFormatInfo:
    """Tests for NumberFormatInfo model."""

    def test_valid_creation_binary_true(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=2)
        assert info.binary is True
        assert info.round_length == 2

    def test_valid_creation_binary_false(self) -> None:
        info = NumberFormatInfo(binary=False, round_length=0)
        assert info.binary is False
        assert info.round_length == 0

    def test_round_trip(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=3)
        json_data = info.model_dump_json()
        restored = NumberFormatInfo.model_validate_json(json_data)
        assert restored.binary == info.binary
        assert restored.round_length == info.round_length
