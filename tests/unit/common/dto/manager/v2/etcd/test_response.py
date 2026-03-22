"""Tests for ai.backend.common.dto.manager.v2.etcd.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.etcd.response import (
    AcceleratorMetadataNode,
    ConfigOkPayload,
    ConfigValuePayload,
    NumberFormatInfo,
    ResourceMetadataPayload,
    ResourceSlotNode,
    VfolderTypesPayload,
)


class TestResourceSlotNode:
    """Tests for ResourceSlotNode model creation and serialization."""

    def test_creation_with_slots(self) -> None:
        node = ResourceSlotNode(slots={"cpu": "count", "mem": "bytes", "cuda.device": "count"})
        assert node.slots == {"cpu": "count", "mem": "bytes", "cuda.device": "count"}

    def test_creation_with_empty_slots(self) -> None:
        node = ResourceSlotNode(slots={})
        assert node.slots == {}

    def test_round_trip(self) -> None:
        node = ResourceSlotNode(slots={"cpu": "count", "mem": "bytes"})
        json_str = node.model_dump_json()
        restored = ResourceSlotNode.model_validate_json(json_str)
        assert restored.slots == node.slots

    def test_json_has_slots_field(self) -> None:
        node = ResourceSlotNode(slots={"cpu": "count"})
        parsed = json.loads(node.model_dump_json())
        assert "slots" in parsed
        assert parsed["slots"]["cpu"] == "count"


class TestNumberFormatInfo:
    """Tests for NumberFormatInfo model creation and serialization."""

    def test_creation_with_binary_true(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=0)
        assert info.binary is True
        assert info.round_length == 0

    def test_creation_with_binary_false(self) -> None:
        info = NumberFormatInfo(binary=False, round_length=2)
        assert info.binary is False
        assert info.round_length == 2

    def test_round_trip_binary_true(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=0)
        json_str = info.model_dump_json()
        restored = NumberFormatInfo.model_validate_json(json_str)
        assert restored.binary is True
        assert restored.round_length == 0

    def test_round_trip_binary_false(self) -> None:
        info = NumberFormatInfo(binary=False, round_length=3)
        json_str = info.model_dump_json()
        restored = NumberFormatInfo.model_validate_json(json_str)
        assert restored.binary is False
        assert restored.round_length == 3

    def test_json_has_expected_fields(self) -> None:
        info = NumberFormatInfo(binary=True, round_length=1)
        parsed = json.loads(info.model_dump_json())
        assert "binary" in parsed
        assert "round_length" in parsed
        assert parsed["binary"] is True
        assert parsed["round_length"] == 1


class TestAcceleratorMetadataNode:
    """Tests for AcceleratorMetadataNode model with nested NumberFormatInfo."""

    def test_creation_with_all_fields(self) -> None:
        number_format = NumberFormatInfo(binary=False, round_length=2)
        node = AcceleratorMetadataNode(
            slot_name="cuda.device",
            description="NVIDIA CUDA GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=number_format,
            display_icon="gpu",
        )
        assert node.slot_name == "cuda.device"
        assert node.description == "NVIDIA CUDA GPU"
        assert node.human_readable_name == "GPU"
        assert node.display_unit == "GPU"
        assert node.number_format.binary is False
        assert node.number_format.round_length == 2
        assert node.display_icon == "gpu"

    def test_nested_number_format_is_preserved(self) -> None:
        number_format = NumberFormatInfo(binary=True, round_length=0)
        node = AcceleratorMetadataNode(
            slot_name="mem",
            description="Memory",
            human_readable_name="RAM",
            display_unit="GiB",
            number_format=number_format,
            display_icon="memory",
        )
        assert node.number_format.binary is True
        assert node.number_format.round_length == 0

    def test_round_trip_preserves_all_fields(self) -> None:
        number_format = NumberFormatInfo(binary=False, round_length=2)
        node = AcceleratorMetadataNode(
            slot_name="cuda.device",
            description="NVIDIA CUDA GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=number_format,
            display_icon="gpu",
        )
        json_str = node.model_dump_json()
        restored = AcceleratorMetadataNode.model_validate_json(json_str)
        assert restored.slot_name == node.slot_name
        assert restored.description == node.description
        assert restored.human_readable_name == node.human_readable_name
        assert restored.display_unit == node.display_unit
        assert restored.display_icon == node.display_icon
        assert restored.number_format.binary == node.number_format.binary
        assert restored.number_format.round_length == node.number_format.round_length

    def test_nested_number_format_in_json(self) -> None:
        number_format = NumberFormatInfo(binary=True, round_length=0)
        node = AcceleratorMetadataNode(
            slot_name="mem",
            description="Memory",
            human_readable_name="RAM",
            display_unit="GiB",
            number_format=number_format,
            display_icon="memory",
        )
        parsed = json.loads(node.model_dump_json())
        assert "number_format" in parsed
        assert isinstance(parsed["number_format"], dict)
        assert parsed["number_format"]["binary"] is True
        assert parsed["number_format"]["round_length"] == 0

    def test_creation_from_dict(self) -> None:
        data = {
            "slot_name": "rocm.device",
            "description": "AMD ROCm GPU",
            "human_readable_name": "GPU",
            "display_unit": "GPU",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "gpu",
        }
        node = AcceleratorMetadataNode.model_validate(data)
        assert node.slot_name == "rocm.device"
        assert node.number_format.binary is False


class TestResourceMetadataPayload:
    """Tests for ResourceMetadataPayload model."""

    def test_creation_with_empty_metadata(self) -> None:
        payload = ResourceMetadataPayload(metadata={})
        assert payload.metadata == {}

    def test_creation_with_single_accelerator(self) -> None:
        number_format = NumberFormatInfo(binary=False, round_length=2)
        node = AcceleratorMetadataNode(
            slot_name="cuda.device",
            description="NVIDIA GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=number_format,
            display_icon="gpu",
        )
        payload = ResourceMetadataPayload(metadata={"cuda.device": node})
        assert "cuda.device" in payload.metadata
        assert payload.metadata["cuda.device"].slot_name == "cuda.device"

    def test_creation_with_multiple_accelerators(self) -> None:
        fmt = NumberFormatInfo(binary=False, round_length=0)
        gpu_node = AcceleratorMetadataNode(
            slot_name="cuda.device",
            description="NVIDIA GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=fmt,
            display_icon="gpu",
        )
        cpu_node = AcceleratorMetadataNode(
            slot_name="cpu",
            description="CPU Cores",
            human_readable_name="CPU",
            display_unit="Core",
            number_format=fmt,
            display_icon="cpu",
        )
        payload = ResourceMetadataPayload(metadata={"cuda.device": gpu_node, "cpu": cpu_node})
        assert len(payload.metadata) == 2

    def test_round_trip(self) -> None:
        fmt = NumberFormatInfo(binary=True, round_length=0)
        node = AcceleratorMetadataNode(
            slot_name="cuda.device",
            description="NVIDIA GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=fmt,
            display_icon="gpu",
        )
        payload = ResourceMetadataPayload(metadata={"cuda.device": node})
        json_str = payload.model_dump_json()
        restored = ResourceMetadataPayload.model_validate_json(json_str)
        assert "cuda.device" in restored.metadata
        assert restored.metadata["cuda.device"].slot_name == "cuda.device"
        assert restored.metadata["cuda.device"].number_format.binary is True

    def test_metadata_values_in_json_are_nested(self) -> None:
        fmt = NumberFormatInfo(binary=False, round_length=2)
        node = AcceleratorMetadataNode(
            slot_name="rocm.device",
            description="AMD GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=fmt,
            display_icon="gpu",
        )
        payload = ResourceMetadataPayload(metadata={"rocm.device": node})
        parsed = json.loads(payload.model_dump_json())
        assert "metadata" in parsed
        assert "rocm.device" in parsed["metadata"]
        assert "number_format" in parsed["metadata"]["rocm.device"]


class TestVfolderTypesPayload:
    """Tests for VfolderTypesPayload model."""

    def test_creation_with_types(self) -> None:
        payload = VfolderTypesPayload(types=["user", "group", "domain"])
        assert payload.types == ["user", "group", "domain"]

    def test_creation_with_empty_types(self) -> None:
        payload = VfolderTypesPayload(types=[])
        assert payload.types == []

    def test_round_trip(self) -> None:
        payload = VfolderTypesPayload(types=["user", "group"])
        json_str = payload.model_dump_json()
        restored = VfolderTypesPayload.model_validate_json(json_str)
        assert restored.types == ["user", "group"]

    def test_json_has_types_field(self) -> None:
        payload = VfolderTypesPayload(types=["user"])
        parsed = json.loads(payload.model_dump_json())
        assert "types" in parsed
        assert isinstance(parsed["types"], list)


class TestConfigValuePayload:
    """Tests for ConfigValuePayload model."""

    def test_creation_with_string_result(self) -> None:
        payload = ConfigValuePayload(result="some_value")
        assert payload.result == "some_value"

    def test_creation_with_dict_result(self) -> None:
        payload = ConfigValuePayload(result={"key": "value"})
        assert payload.result == {"key": "value"}

    def test_creation_with_none_result(self) -> None:
        payload = ConfigValuePayload(result=None)
        assert payload.result is None

    def test_creation_with_integer_result(self) -> None:
        payload = ConfigValuePayload(result=42)
        assert payload.result == 42

    def test_round_trip_with_string(self) -> None:
        payload = ConfigValuePayload(result="test_value")
        json_str = payload.model_dump_json()
        restored = ConfigValuePayload.model_validate_json(json_str)
        assert restored.result == "test_value"

    def test_round_trip_with_dict(self) -> None:
        payload = ConfigValuePayload(result={"a": 1, "b": [1, 2, 3]})
        json_str = payload.model_dump_json()
        restored = ConfigValuePayload.model_validate_json(json_str)
        assert restored.result == {"a": 1, "b": [1, 2, 3]}


class TestConfigOkPayload:
    """Tests for ConfigOkPayload model."""

    def test_default_result_is_ok(self) -> None:
        payload = ConfigOkPayload()
        assert payload.result == "ok"

    def test_creation_without_arguments(self) -> None:
        payload = ConfigOkPayload()
        assert payload is not None

    def test_result_can_be_overridden(self) -> None:
        payload = ConfigOkPayload(result="done")
        assert payload.result == "done"

    def test_round_trip_with_default(self) -> None:
        payload = ConfigOkPayload()
        json_str = payload.model_dump_json()
        restored = ConfigOkPayload.model_validate_json(json_str)
        assert restored.result == "ok"

    def test_round_trip_with_custom_result(self) -> None:
        payload = ConfigOkPayload(result="success")
        json_str = payload.model_dump_json()
        restored = ConfigOkPayload.model_validate_json(json_str)
        assert restored.result == "success"

    def test_json_has_result_field(self) -> None:
        payload = ConfigOkPayload()
        parsed = json.loads(payload.model_dump_json())
        assert "result" in parsed
        assert parsed["result"] == "ok"
