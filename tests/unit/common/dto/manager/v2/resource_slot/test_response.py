"""Tests for ai.backend.common.dto.manager.v2.resource_slot.response module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInfo


def _make_resource_slot_type_node(slot_name: str = "cpu") -> ResourceSlotTypeNode:
    return ResourceSlotTypeNode(
        slot_name=slot_name,
        slot_type="count",
        display_name="CPU",
        description="CPU cores",
        display_unit="cores",
        display_icon="cpu",
        number_format=NumberFormatInfo(binary=False, round_length=2),
        rank=1,
    )


class TestResourceSlotTypeNode:
    """Tests for ResourceSlotTypeNode model."""

    def test_valid_creation(self) -> None:
        node = _make_resource_slot_type_node()
        assert node.slot_name == "cpu"
        assert node.slot_type == "count"
        assert node.display_name == "CPU"
        assert node.rank == 1

    def test_nested_number_format(self) -> None:
        node = _make_resource_slot_type_node()
        assert node.number_format.binary is False
        assert node.number_format.round_length == 2

    def test_memory_slot(self) -> None:
        node = ResourceSlotTypeNode(
            slot_name="mem",
            slot_type="bytes",
            display_name="Memory",
            description="RAM",
            display_unit="GiB",
            display_icon="memory",
            number_format=NumberFormatInfo(binary=True, round_length=2),
            rank=2,
        )
        assert node.slot_name == "mem"
        assert node.number_format.binary is True

    def test_serializes_correctly(self) -> None:
        node = _make_resource_slot_type_node()
        data = node.model_dump()
        assert "slot_name" in data
        assert "number_format" in data
        assert data["number_format"]["binary"] is False

    def test_round_trip(self) -> None:
        node = _make_resource_slot_type_node()
        json_data = node.model_dump_json()
        restored = ResourceSlotTypeNode.model_validate_json(json_data)
        assert restored.slot_name == node.slot_name
        assert restored.number_format.binary == node.number_format.binary
        assert restored.number_format.round_length == node.number_format.round_length

    def test_cuda_slot(self) -> None:
        node = ResourceSlotTypeNode(
            slot_name="cuda.device",
            slot_type="unique-count",
            display_name="GPU",
            description="NVIDIA GPU",
            display_unit="devices",
            display_icon="gpu",
            number_format=NumberFormatInfo(binary=False, round_length=0),
            rank=3,
        )
        assert node.slot_name == "cuda.device"
        assert node.slot_type == "unique-count"
