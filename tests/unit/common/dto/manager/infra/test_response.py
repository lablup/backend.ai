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
    def test_creation(self) -> None:
        resp = GetResourceSlotsResponse(
            resource_slots={"cpu": "count", "mem": "bytes", "cuda.device": "count"}
        )
        assert "cpu" in resp.resource_slots
        assert resp.resource_slots["mem"] == "bytes"

    def test_empty_slots(self) -> None:
        resp = GetResourceSlotsResponse(resource_slots={})
        assert resp.resource_slots == {}


class TestGetResourceMetadataResponse:
    def test_creation(self) -> None:
        resp = GetResourceMetadataResponse(
            accelerator_metadata={
                "cpu": AcceleratorMetadataDTO(
                    slot_name="cpu",
                    description="CPU",
                    human_readable_name="CPU",
                    display_unit="Core",
                    number_format=NumberFormatDTO(binary=False, round_length=0),
                    display_icon="cpu",
                ),
            }
        )
        assert "cpu" in resp.accelerator_metadata
        assert resp.accelerator_metadata["cpu"].display_unit == "Core"


class TestGetVFolderTypesResponse:
    def test_creation(self) -> None:
        resp = GetVFolderTypesResponse(vfolder_types=["user", "group"])
        assert len(resp.vfolder_types) == 2

    def test_empty_list(self) -> None:
        resp = GetVFolderTypesResponse(vfolder_types=[])
        assert resp.vfolder_types == []


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
    def test_creation(self) -> None:
        resp = UsagePerMonthResponse(result=[{"session_id": "s1", "cpu_used": 100}])
        assert len(resp.result) == 1

    def test_empty_result(self) -> None:
        resp = UsagePerMonthResponse(result=[])
        assert resp.result == []


class TestUsagePerPeriodResponse:
    def test_creation(self) -> None:
        resp = UsagePerPeriodResponse(result=[{"date": "20200601", "count": 5}])
        assert len(resp.result) == 1


class TestMonthStatsResponse:
    def test_creation(self) -> None:
        resp = MonthStatsResponse(stats=[{"timestamp": "2020-06-01T00:00:00", "count": 3}])
        assert len(resp.stats) == 1

    def test_empty_stats(self) -> None:
        resp = MonthStatsResponse(stats=[])
        assert resp.stats == []


class TestWatcherStatusResponse:
    def test_creation(self) -> None:
        resp = WatcherStatusResponse(data={"status": "running", "uptime": 3600})
        assert resp.data["status"] == "running"


class TestWatcherAgentActionResponse:
    def test_creation(self) -> None:
        resp = WatcherAgentActionResponse(data={"result": "ok"})
        assert resp.data["result"] == "ok"


class TestGetContainerRegistriesResponse:
    def test_creation(self) -> None:
        resp = GetContainerRegistriesResponse(
            registries={
                "cr.backend.ai": {"type": "harbor2", "url": "https://cr.backend.ai"},
            }
        )
        assert "cr.backend.ai" in resp.registries

    def test_empty_registries(self) -> None:
        resp = GetContainerRegistriesResponse(registries={})
        assert resp.registries == {}


class TestFieldDescriptions:
    """Verify all response models have descriptions for their fields."""

    @pytest.mark.parametrize(
        "model_cls",
        [
            GetResourceSlotsResponse,
            GetResourceMetadataResponse,
            GetVFolderTypesResponse,
            GetConfigResponse,
            SetConfigResponse,
            DeleteConfigResponse,
            ListScalingGroupsResponse,
            GetWSProxyVersionResponse,
            ListPresetsResponse,
            CheckPresetsResponse,
            UsagePerMonthResponse,
            UsagePerPeriodResponse,
            MonthStatsResponse,
            WatcherStatusResponse,
            WatcherAgentActionResponse,
            GetContainerRegistriesResponse,
        ],
    )
    def test_all_fields_have_descriptions(self, model_cls: type[BaseModel]) -> None:
        schema = model_cls.model_json_schema()
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            assert "description" in field_schema, (
                f"{model_cls.__name__}.{field_name} is missing a description"
            )
