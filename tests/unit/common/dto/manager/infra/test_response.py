"""
Unit tests for Infrastructure response DTOs.
"""

from __future__ import annotations

from typing import Any

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


# --- etcd responses (BaseRootResponseModel — bare JSON) ---


class TestGetResourceSlotsResponse:
    """Handler returns bare dict: ``{str(k): v for k, v in known_slots.items()}``"""

    def test_bare_dict_input(self) -> None:
        raw: dict[str, str] = {"cpu": "count", "mem": "bytes", "cuda.device": "count"}
        resp = GetResourceSlotsResponse.model_validate(raw)
        assert "cpu" in resp.root
        assert resp.root["mem"] == "bytes"

    def test_empty_slots(self) -> None:
        resp = GetResourceSlotsResponse.model_validate({})
        assert resp.root == {}

    def test_model_dump_matches_server_response(self) -> None:
        raw: dict[str, str] = {"cpu": "count", "mem": "bytes"}
        resp = GetResourceSlotsResponse.model_validate(raw)
        assert resp.model_dump() == raw

    def test_serialization_roundtrip(self) -> None:
        raw: dict[str, str] = {"cpu": "count", "mem": "bytes"}
        resp = GetResourceSlotsResponse.model_validate(raw)
        dumped = resp.model_dump()
        restored = GetResourceSlotsResponse.model_validate(dumped)
        assert restored.root == raw


class TestGetResourceMetadataResponse:
    """Handler returns bare dict of accelerator metadata."""

    def test_bare_dict_input(self) -> None:
        raw = {
            "cpu": {
                "slot_name": "cpu",
                "description": "CPU",
                "human_readable_name": "CPU",
                "display_unit": "Core",
                "number_format": {"binary": False, "round_length": 0},
                "display_icon": "cpu",
            },
        }
        resp = GetResourceMetadataResponse.model_validate(raw)
        assert "cpu" in resp.root
        assert resp.root["cpu"].display_unit == "Core"

    def test_model_dump_matches_server_response(self) -> None:
        raw = {
            "cpu": {
                "slot_name": "cpu",
                "description": "CPU",
                "human_readable_name": "CPU",
                "display_unit": "Core",
                "number_format": {"binary": False, "round_length": 0},
                "display_icon": "cpu",
            },
        }
        resp = GetResourceMetadataResponse.model_validate(raw)
        assert resp.model_dump() == raw


class TestGetVFolderTypesResponse:
    """Handler returns bare list: ``vfolder_types``."""

    def test_bare_list_input(self) -> None:
        raw = ["user", "group"]
        resp = GetVFolderTypesResponse.model_validate(raw)
        assert resp.root == ["user", "group"]

    def test_empty_list(self) -> None:
        resp = GetVFolderTypesResponse.model_validate([])
        assert resp.root == []

    def test_model_dump_matches_server_response(self) -> None:
        raw = ["user", "group"]
        resp = GetVFolderTypesResponse.model_validate(raw)
        assert resp.model_dump() == raw

    def test_serialization_roundtrip(self) -> None:
        raw = ["user", "group"]
        resp = GetVFolderTypesResponse.model_validate(raw)
        dumped = resp.model_dump()
        restored = GetVFolderTypesResponse.model_validate(dumped)
        assert restored.root == raw


# --- etcd responses (BaseResponseModel — structured JSON) ---


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


# --- scaling_group responses (BaseResponseModel — structured JSON) ---


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


# --- resource responses (BaseResponseModel — structured JSON) ---


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


# --- resource responses (BaseRootResponseModel — bare JSON) ---


class TestUsagePerMonthResponse:
    """Handler returns bare list: ``result.result``."""

    def test_bare_list_input(self) -> None:
        raw: list[Any] = [{"session_id": "s1", "cpu_used": 100}]
        resp = UsagePerMonthResponse.model_validate(raw)
        assert len(resp.root) == 1

    def test_empty_result(self) -> None:
        resp = UsagePerMonthResponse.model_validate([])
        assert resp.root == []

    def test_model_dump_matches_server_response(self) -> None:
        raw: list[Any] = [{"session_id": "s1", "cpu_used": 100}]
        resp = UsagePerMonthResponse.model_validate(raw)
        assert resp.model_dump() == raw

    def test_serialization_roundtrip(self) -> None:
        raw: list[Any] = [{"session_id": "s1", "cpu_used": 100}]
        resp = UsagePerMonthResponse.model_validate(raw)
        dumped = resp.model_dump()
        restored = UsagePerMonthResponse.model_validate(dumped)
        assert restored.root == raw


class TestUsagePerPeriodResponse:
    """Handler returns bare list: ``result.result``."""

    def test_bare_list_input(self) -> None:
        raw: list[Any] = [{"date": "20200601", "count": 5}]
        resp = UsagePerPeriodResponse.model_validate(raw)
        assert len(resp.root) == 1

    def test_model_dump_matches_server_response(self) -> None:
        raw: list[Any] = [{"date": "20200601", "count": 5}]
        resp = UsagePerPeriodResponse.model_validate(raw)
        assert resp.model_dump() == raw


class TestMonthStatsResponse:
    """Handler returns bare list: ``result.stats``."""

    def test_bare_list_input(self) -> None:
        raw: list[Any] = [{"timestamp": "2020-06-01T00:00:00", "count": 3}]
        resp = MonthStatsResponse.model_validate(raw)
        assert len(resp.root) == 1

    def test_empty_stats(self) -> None:
        resp = MonthStatsResponse.model_validate([])
        assert resp.root == []

    def test_model_dump_matches_server_response(self) -> None:
        raw: list[Any] = [{"timestamp": "2020-06-01T00:00:00", "count": 3}]
        resp = MonthStatsResponse.model_validate(raw)
        assert resp.model_dump() == raw


class TestWatcherStatusResponse:
    """Handler returns bare dict: ``result.data``."""

    def test_bare_dict_input(self) -> None:
        raw: dict[str, Any] = {"status": "running", "uptime": 3600}
        resp = WatcherStatusResponse.model_validate(raw)
        assert resp.root["status"] == "running"

    def test_model_dump_matches_server_response(self) -> None:
        raw: dict[str, Any] = {"status": "running", "uptime": 3600}
        resp = WatcherStatusResponse.model_validate(raw)
        assert resp.model_dump() == raw


class TestWatcherAgentActionResponse:
    """Handler returns bare dict: ``result.data``."""

    def test_bare_dict_input(self) -> None:
        raw: dict[str, Any] = {"result": "ok"}
        resp = WatcherAgentActionResponse.model_validate(raw)
        assert resp.root["result"] == "ok"

    def test_model_dump_matches_server_response(self) -> None:
        raw: dict[str, Any] = {"result": "ok"}
        resp = WatcherAgentActionResponse.model_validate(raw)
        assert resp.model_dump() == raw


class TestGetContainerRegistriesResponse:
    """Handler returns bare dict: ``result.registries``."""

    def test_bare_dict_input(self) -> None:
        raw: dict[str, Any] = {
            "cr.backend.ai": {"type": "harbor2", "url": "https://cr.backend.ai"},
        }
        resp = GetContainerRegistriesResponse.model_validate(raw)
        assert "cr.backend.ai" in resp.root

    def test_empty_registries(self) -> None:
        resp = GetContainerRegistriesResponse.model_validate({})
        assert resp.root == {}

    def test_model_dump_matches_server_response(self) -> None:
        raw: dict[str, Any] = {
            "cr.backend.ai": {"type": "harbor2", "url": "https://cr.backend.ai"},
        }
        resp = GetContainerRegistriesResponse.model_validate(raw)
        assert resp.model_dump() == raw
