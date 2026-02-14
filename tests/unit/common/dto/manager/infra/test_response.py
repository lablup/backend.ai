"""
Unit tests for Infrastructure response DTOs.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from ai.backend.common.dto.manager.infra.response import (
    AcceleratorMetadataDTO,
    CheckPresetsResponse,
    DeleteConfigResponse,
    GetConfigResponse,
    GetContainerRegistriesResponse,
    GetResourceMetadataResponse,
    GetResourceSlotsResponse,
    GetVFolderTypesResponse,
    GetWSProxyVersionResponse,
    ListPresetsResponse,
    ListScalingGroupsResponse,
    MonthStatsResponse,
    NumberFormatDTO,
    RecalculateUsageResponse,
    ResourcePresetDTO,
    ScalingGroupDTO,
    SetConfigResponse,
    UsagePerMonthResponse,
    UsagePerPeriodResponse,
    WatcherAgentActionResponse,
    WatcherStatusResponse,
)

# --- Nested DTOs ---


class TestNumberFormatDTO:
    def test_creation(self) -> None:
        nf = NumberFormatDTO(binary=True, round_length=2)
        assert nf.binary is True
        assert nf.round_length == 2


class TestAcceleratorMetadataDTO:
    def test_creation(self) -> None:
        meta = AcceleratorMetadataDTO(
            slot_name="cuda.device",
            description="CUDA-capable GPU",
            human_readable_name="GPU",
            display_unit="GPU",
            number_format=NumberFormatDTO(binary=False, round_length=0),
            display_icon="gpu1",
        )
        assert meta.slot_name == "cuda.device"
        assert meta.number_format.binary is False

    def test_serialization_roundtrip(self) -> None:
        meta = AcceleratorMetadataDTO(
            slot_name="cpu",
            description="CPU",
            human_readable_name="CPU",
            display_unit="Core",
            number_format=NumberFormatDTO(binary=False, round_length=0),
            display_icon="cpu",
        )
        json_str = meta.model_dump_json()
        restored = AcceleratorMetadataDTO.model_validate_json(json_str)
        assert restored.slot_name == meta.slot_name
        assert restored.number_format.round_length == 0


class TestScalingGroupDTO:
    def test_creation(self) -> None:
        sg = ScalingGroupDTO(name="default")
        assert sg.name == "default"


class TestResourcePresetDTO:
    def test_creation(self) -> None:
        preset = ResourcePresetDTO(
            name="small",
            resource_slots={"cpu": "1", "mem": "1073741824"},
        )
        assert preset.name == "small"
        assert preset.shared_memory is None

    def test_with_shared_memory(self) -> None:
        preset = ResourcePresetDTO(
            name="large",
            resource_slots={"cpu": "4", "mem": "4294967296"},
            shared_memory="1g",
        )
        assert preset.shared_memory == "1g"


# --- etcd responses ---


class TestGetResourceSlotsResponse:
    """Handler returns bare dict: ``{str(k): v for k, v in known_slots.items()}``"""

    def test_creation(self) -> None:
        resp = GetResourceSlotsResponse({"cpu": "count", "mem": "bytes", "cuda.device": "count"})
        assert "cpu" in resp.root
        assert resp.root["mem"] == "bytes"

    def test_empty_slots(self) -> None:
        resp = GetResourceSlotsResponse({})
        assert resp.root == {}

    def test_serialization_roundtrip(self) -> None:
        data = {"cpu": "count", "mem": "bytes"}
        resp = GetResourceSlotsResponse(data)
        json_str = resp.model_dump_json()
        restored = GetResourceSlotsResponse.model_validate_json(json_str)
        assert restored.root == data


class TestGetResourceMetadataResponse:
    """Handler returns bare dict of accelerator metadata."""

    def test_creation(self) -> None:
        resp = GetResourceMetadataResponse({
            "cpu": AcceleratorMetadataDTO(
                slot_name="cpu",
                description="CPU",
                human_readable_name="CPU",
                display_unit="Core",
                number_format=NumberFormatDTO(binary=False, round_length=0),
                display_icon="cpu",
            ),
        })
        assert "cpu" in resp.root
        assert resp.root["cpu"].display_unit == "Core"

    def test_from_raw_dict(self) -> None:
        """Verify construction from raw dict (as handler returns)."""
        resp = GetResourceMetadataResponse.model_validate({
            "cpu": {
                "slot_name": "cpu",
                "description": "CPU",
                "human_readable_name": "CPU",
                "display_unit": "Core",
                "number_format": {"binary": False, "round_length": 0},
                "display_icon": "cpu",
            },
        })
        assert resp.root["cpu"].slot_name == "cpu"


class TestGetVFolderTypesResponse:
    """Handler returns bare list: ``vfolder_types``."""

    def test_creation(self) -> None:
        resp = GetVFolderTypesResponse(["user", "group"])
        assert len(resp.root) == 2

    def test_empty_list(self) -> None:
        resp = GetVFolderTypesResponse([])
        assert resp.root == []

    def test_serialization_roundtrip(self) -> None:
        data = ["user", "group"]
        resp = GetVFolderTypesResponse(data)
        json_str = resp.model_dump_json()
        restored = GetVFolderTypesResponse.model_validate_json(json_str)
        assert restored.root == data


class TestGetConfigResponse:
    def test_scalar_result(self) -> None:
        resp = GetConfigResponse(result="some_value")
        assert resp.result == "some_value"

    def test_dict_result(self) -> None:
        resp = GetConfigResponse(result={"nested": {"key": "value"}})
        assert resp.result["nested"]["key"] == "value"

    def test_null_result(self) -> None:
        resp = GetConfigResponse(result=None)
        assert resp.result is None


class TestSetConfigResponse:
    def test_creation(self) -> None:
        resp = SetConfigResponse(result="ok")
        assert resp.result == "ok"


class TestDeleteConfigResponse:
    def test_creation(self) -> None:
        resp = DeleteConfigResponse(result="ok")
        assert resp.result == "ok"


# --- scaling_group responses ---


class TestListScalingGroupsResponse:
    def test_creation(self) -> None:
        resp = ListScalingGroupsResponse(
            scaling_groups=[ScalingGroupDTO(name="default"), ScalingGroupDTO(name="gpu")]
        )
        assert len(resp.scaling_groups) == 2
        assert resp.scaling_groups[0].name == "default"

    def test_empty_list(self) -> None:
        resp = ListScalingGroupsResponse(scaling_groups=[])
        assert resp.scaling_groups == []

    def test_serialization_roundtrip(self) -> None:
        resp = ListScalingGroupsResponse(
            scaling_groups=[ScalingGroupDTO(name="sg1")],
        )
        json_str = resp.model_dump_json()
        restored = ListScalingGroupsResponse.model_validate_json(json_str)
        assert restored.scaling_groups[0].name == "sg1"


class TestGetWSProxyVersionResponse:
    def test_creation(self) -> None:
        resp = GetWSProxyVersionResponse(wsproxy_version=2)
        assert resp.wsproxy_version == 2


# --- resource responses ---


class TestListPresetsResponse:
    def test_creation(self) -> None:
        resp = ListPresetsResponse(presets=[{"name": "small", "resource_slots": {"cpu": "1"}}])
        assert len(resp.presets) == 1

    def test_empty_presets(self) -> None:
        resp = ListPresetsResponse(presets=[])
        assert resp.presets == []


class TestCheckPresetsResponse:
    def test_creation(self) -> None:
        resp = CheckPresetsResponse(
            presets=[{"name": "small", "allocatable": True}],
            keypair_limits={"cpu": "4"},
            keypair_using={"cpu": "1"},
            keypair_remaining={"cpu": "3"},
            group_limits={"cpu": "8"},
            group_using={"cpu": "2"},
            group_remaining={"cpu": "6"},
            scaling_group_remaining={"cpu": "10"},
            scaling_groups={
                "default": {
                    "occupied": {"cpu": "2"},
                    "available": {"cpu": "10"},
                }
            },
        )
        assert len(resp.presets) == 1
        assert resp.keypair_limits["cpu"] == "4"
        assert "default" in resp.scaling_groups


class TestRecalculateUsageResponse:
    def test_creation(self) -> None:
        resp = RecalculateUsageResponse()
        assert resp is not None


class TestUsagePerMonthResponse:
    """Handler returns bare list: ``result.result``."""

    def test_creation(self) -> None:
        resp = UsagePerMonthResponse([{"session_id": "s1", "cpu_used": 100}])
        assert len(resp.root) == 1

    def test_empty_result(self) -> None:
        resp = UsagePerMonthResponse([])
        assert resp.root == []

    def test_serialization_roundtrip(self) -> None:
        data = [{"session_id": "s1", "cpu_used": 100}]
        resp = UsagePerMonthResponse(data)
        json_str = resp.model_dump_json()
        restored = UsagePerMonthResponse.model_validate_json(json_str)
        assert restored.root == data


class TestUsagePerPeriodResponse:
    """Handler returns bare list: ``result.result``."""

    def test_creation(self) -> None:
        resp = UsagePerPeriodResponse([{"date": "20200601", "count": 5}])
        assert len(resp.root) == 1


class TestMonthStatsResponse:
    """Handler returns bare list: ``result.stats``."""

    def test_creation(self) -> None:
        resp = MonthStatsResponse([{"timestamp": "2020-06-01T00:00:00", "count": 3}])
        assert len(resp.root) == 1

    def test_empty_stats(self) -> None:
        resp = MonthStatsResponse([])
        assert resp.root == []


class TestWatcherStatusResponse:
    """Handler returns bare dict: ``result.data``."""

    def test_creation(self) -> None:
        resp = WatcherStatusResponse({"status": "running", "uptime": 3600})
        assert resp.root["status"] == "running"


class TestWatcherAgentActionResponse:
    """Handler returns bare dict: ``result.data``."""

    def test_creation(self) -> None:
        resp = WatcherAgentActionResponse({"result": "ok"})
        assert resp.root["result"] == "ok"


class TestGetContainerRegistriesResponse:
    """Handler returns bare dict: ``result.registries``."""

    def test_creation(self) -> None:
        resp = GetContainerRegistriesResponse({
            "cr.backend.ai": {"type": "harbor2", "url": "https://cr.backend.ai"},
        })
        assert "cr.backend.ai" in resp.root

    def test_empty_registries(self) -> None:
        resp = GetContainerRegistriesResponse({})
        assert resp.root == {}


class TestFieldDescriptions:
    """Verify all non-RootModel response models have descriptions for their fields."""

    @pytest.mark.parametrize(
        "model_cls",
        [
            GetConfigResponse,
            SetConfigResponse,
            DeleteConfigResponse,
            ListScalingGroupsResponse,
            GetWSProxyVersionResponse,
            ListPresetsResponse,
            CheckPresetsResponse,
        ],
    )
    def test_all_fields_have_descriptions(self, model_cls: type[BaseModel]) -> None:
        schema = model_cls.model_json_schema()
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            assert "description" in field_schema, (
                f"{model_cls.__name__}.{field_name} is missing a description"
            )
