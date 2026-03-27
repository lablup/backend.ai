"""Tests for ai.backend.common.dto.manager.v2.infra.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.infra.response import (
    CheckPresetsPayload,
    ContainerRegistriesPayload,
    ListPresetsPayload,
    ListScalingGroupsPayload,
    ResourcePresetNode,
    ScalingGroupNode,
    UsagePayload,
    WatcherActionPayload,
    WatcherStatusPayload,
    WSProxyVersionPayload,
)


class TestScalingGroupNode:
    """Tests for ScalingGroupNode model."""

    def test_creation_with_name(self) -> None:
        node = ScalingGroupNode(name="gpu-cluster")
        assert node.name == "gpu-cluster"

    def test_name_is_string(self) -> None:
        node = ScalingGroupNode(name="default")
        assert isinstance(node.name, str)

    def test_round_trip_preserves_name(self) -> None:
        node = ScalingGroupNode(name="cpu-only")
        json_str = node.model_dump_json()
        restored = ScalingGroupNode.model_validate_json(json_str)
        assert restored.name == node.name

    def test_json_has_name_field(self) -> None:
        node = ScalingGroupNode(name="gpu-cluster")
        parsed = json.loads(node.model_dump_json())
        assert "name" in parsed
        assert parsed["name"] == "gpu-cluster"

    def test_creation_from_dict(self) -> None:
        node = ScalingGroupNode.model_validate({"name": "research"})
        assert node.name == "research"


class TestResourcePresetNode:
    """Tests for ResourcePresetNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = ResourcePresetNode(
            name="small-gpu",
            resource_slots={"cpu": "2", "mem": "4g", "cuda.device": "1"},
        )
        assert node.name == "small-gpu"
        assert node.resource_slots == {"cpu": "2", "mem": "4g", "cuda.device": "1"}
        assert node.shared_memory is None

    def test_creation_with_shared_memory(self) -> None:
        node = ResourcePresetNode(
            name="large-gpu",
            resource_slots={"cpu": "8", "mem": "32g"},
            shared_memory="4g",
        )
        assert node.shared_memory == "4g"

    def test_default_shared_memory_is_none(self) -> None:
        node = ResourcePresetNode(name="preset", resource_slots={})
        assert node.shared_memory is None

    def test_round_trip_preserves_all_fields(self) -> None:
        node = ResourcePresetNode(
            name="standard",
            resource_slots={"cpu": "4", "mem": "16g"},
            shared_memory="2g",
        )
        json_str = node.model_dump_json()
        restored = ResourcePresetNode.model_validate_json(json_str)
        assert restored.name == node.name
        assert restored.resource_slots == node.resource_slots
        assert restored.shared_memory == node.shared_memory

    def test_round_trip_with_null_shared_memory(self) -> None:
        node = ResourcePresetNode(name="preset", resource_slots={"cpu": "1"})
        json_str = node.model_dump_json()
        restored = ResourcePresetNode.model_validate_json(json_str)
        assert restored.shared_memory is None

    def test_resource_slots_is_dict(self) -> None:
        node = ResourcePresetNode(name="x", resource_slots={"cpu": "2"})
        assert isinstance(node.resource_slots, dict)


class TestListScalingGroupsPayload:
    """Tests for ListScalingGroupsPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = ListScalingGroupsPayload(scaling_groups=[])
        assert payload.scaling_groups == []

    def test_creation_with_scaling_groups(self) -> None:
        groups = [ScalingGroupNode(name="g1"), ScalingGroupNode(name="g2")]
        payload = ListScalingGroupsPayload(scaling_groups=groups)
        assert len(payload.scaling_groups) == 2
        assert payload.scaling_groups[0].name == "g1"
        assert payload.scaling_groups[1].name == "g2"

    def test_round_trip_preserves_groups(self) -> None:
        groups = [ScalingGroupNode(name="gpu"), ScalingGroupNode(name="cpu")]
        payload = ListScalingGroupsPayload(scaling_groups=groups)
        json_str = payload.model_dump_json()
        restored = ListScalingGroupsPayload.model_validate_json(json_str)
        assert len(restored.scaling_groups) == 2
        assert restored.scaling_groups[0].name == "gpu"

    def test_json_has_scaling_groups_key(self) -> None:
        payload = ListScalingGroupsPayload(scaling_groups=[])
        parsed = json.loads(payload.model_dump_json())
        assert "scaling_groups" in parsed


class TestWSProxyVersionPayload:
    """Tests for WSProxyVersionPayload model."""

    def test_creation_with_version(self) -> None:
        payload = WSProxyVersionPayload(wsproxy_version=2)
        assert payload.wsproxy_version == 2

    def test_wsproxy_version_is_int(self) -> None:
        payload = WSProxyVersionPayload(wsproxy_version=3)
        assert isinstance(payload.wsproxy_version, int)

    def test_round_trip_preserves_version(self) -> None:
        payload = WSProxyVersionPayload(wsproxy_version=5)
        json_str = payload.model_dump_json()
        restored = WSProxyVersionPayload.model_validate_json(json_str)
        assert restored.wsproxy_version == 5


class TestListPresetsPayload:
    """Tests for ListPresetsPayload model."""

    def test_creation_with_empty_presets(self) -> None:
        payload = ListPresetsPayload(presets=[])
        assert payload.presets == []

    def test_creation_with_presets(self) -> None:
        presets = [{"name": "small", "cpu": "2"}, {"name": "large", "cpu": "8"}]
        payload = ListPresetsPayload(presets=presets)
        assert len(payload.presets) == 2

    def test_round_trip_preserves_presets(self) -> None:
        presets = [{"name": "small", "resource_slots": {"cpu": "2"}}]
        payload = ListPresetsPayload(presets=presets)
        json_str = payload.model_dump_json()
        restored = ListPresetsPayload.model_validate_json(json_str)
        assert len(restored.presets) == 1
        assert restored.presets[0]["name"] == "small"


class TestCheckPresetsPayload:
    """Tests for CheckPresetsPayload model — verifies all resource limit fields are present."""

    def _make_payload(self) -> CheckPresetsPayload:
        return CheckPresetsPayload(
            presets=[{"name": "small", "allocatable": True}],
            keypair_limits={"cpu": "10", "mem": "50g"},
            keypair_using={"cpu": "2", "mem": "8g"},
            keypair_remaining={"cpu": "8", "mem": "42g"},
            group_limits={"cpu": "100", "mem": "500g"},
            group_using={"cpu": "20", "mem": "80g"},
            group_remaining={"cpu": "80", "mem": "420g"},
            scaling_group_remaining={"cpu": "50", "mem": "200g"},
            scaling_groups={"default": {"remaining": {"cpu": "50"}}},
        )

    def test_creation_with_all_fields(self) -> None:
        payload = self._make_payload()
        assert len(payload.presets) == 1
        assert payload.keypair_limits == {"cpu": "10", "mem": "50g"}
        assert payload.keypair_using == {"cpu": "2", "mem": "8g"}
        assert payload.keypair_remaining == {"cpu": "8", "mem": "42g"}
        assert payload.group_limits == {"cpu": "100", "mem": "500g"}
        assert payload.group_using == {"cpu": "20", "mem": "80g"}
        assert payload.group_remaining == {"cpu": "80", "mem": "420g"}
        assert payload.scaling_group_remaining == {"cpu": "50", "mem": "200g"}
        assert "default" in payload.scaling_groups

    def test_has_all_required_fields(self) -> None:
        payload = self._make_payload()
        assert hasattr(payload, "presets")
        assert hasattr(payload, "keypair_limits")
        assert hasattr(payload, "keypair_using")
        assert hasattr(payload, "keypair_remaining")
        assert hasattr(payload, "group_limits")
        assert hasattr(payload, "group_using")
        assert hasattr(payload, "group_remaining")
        assert hasattr(payload, "scaling_group_remaining")
        assert hasattr(payload, "scaling_groups")

    def test_round_trip_preserves_all_fields(self) -> None:
        payload = self._make_payload()
        json_str = payload.model_dump_json()
        restored = CheckPresetsPayload.model_validate_json(json_str)
        assert restored.keypair_limits == payload.keypair_limits
        assert restored.keypair_using == payload.keypair_using
        assert restored.keypair_remaining == payload.keypair_remaining
        assert restored.group_limits == payload.group_limits
        assert restored.group_using == payload.group_using
        assert restored.group_remaining == payload.group_remaining
        assert restored.scaling_group_remaining == payload.scaling_group_remaining
        assert restored.scaling_groups == payload.scaling_groups

    def test_json_has_all_resource_limit_keys(self) -> None:
        payload = self._make_payload()
        parsed = json.loads(payload.model_dump_json())
        expected_keys = {
            "presets",
            "keypair_limits",
            "keypair_using",
            "keypair_remaining",
            "group_limits",
            "group_using",
            "group_remaining",
            "scaling_group_remaining",
            "scaling_groups",
        }
        assert expected_keys.issubset(set(parsed.keys()))

    def test_scaling_groups_is_nested_dict(self) -> None:
        payload = self._make_payload()
        assert isinstance(payload.scaling_groups, dict)
        for v in payload.scaling_groups.values():
            assert isinstance(v, dict)


class TestUsagePayload:
    """Tests for UsagePayload model."""

    def test_creation_with_empty_records(self) -> None:
        payload = UsagePayload(records=[])
        assert payload.records == []

    def test_creation_with_records(self) -> None:
        payload = UsagePayload(records=[{"session": "s1", "cpu": 2.5}])
        assert len(payload.records) == 1

    def test_round_trip_preserves_records(self) -> None:
        payload = UsagePayload(records=[{"id": "r1"}, {"id": "r2"}])
        json_str = payload.model_dump_json()
        restored = UsagePayload.model_validate_json(json_str)
        assert len(restored.records) == 2


class TestWatcherStatusPayload:
    """Tests for WatcherStatusPayload model."""

    def test_creation_with_status_dict(self) -> None:
        payload = WatcherStatusPayload(status={"alive": True, "agent_id": "a1"})
        assert payload.status["alive"] is True

    def test_status_is_dict(self) -> None:
        payload = WatcherStatusPayload(status={})
        assert isinstance(payload.status, dict)

    def test_round_trip_preserves_status(self) -> None:
        payload = WatcherStatusPayload(status={"version": "1.0", "running": True})
        json_str = payload.model_dump_json()
        restored = WatcherStatusPayload.model_validate_json(json_str)
        assert restored.status == payload.status


class TestWatcherActionPayload:
    """Tests for WatcherActionPayload model."""

    def test_creation_with_result_dict(self) -> None:
        payload = WatcherActionPayload(result={"ok": True})
        assert payload.result["ok"] is True

    def test_result_is_dict(self) -> None:
        payload = WatcherActionPayload(result={})
        assert isinstance(payload.result, dict)

    def test_round_trip_preserves_result(self) -> None:
        payload = WatcherActionPayload(result={"action": "restart", "status": "done"})
        json_str = payload.model_dump_json()
        restored = WatcherActionPayload.model_validate_json(json_str)
        assert restored.result == payload.result


class TestContainerRegistriesPayload:
    """Tests for ContainerRegistriesPayload model."""

    def test_creation_with_empty_registries(self) -> None:
        payload = ContainerRegistriesPayload(registries={})
        assert payload.registries == {}

    def test_creation_with_registries(self) -> None:
        payload = ContainerRegistriesPayload(
            registries={"docker.io": {"username": "user", "password": "***"}}
        )
        assert "docker.io" in payload.registries

    def test_round_trip_preserves_registries(self) -> None:
        payload = ContainerRegistriesPayload(
            registries={"registry.example.com": {"type": "docker"}}
        )
        json_str = payload.model_dump_json()
        restored = ContainerRegistriesPayload.model_validate_json(json_str)
        assert restored.registries == payload.registries

    def test_registries_is_dict(self) -> None:
        payload = ContainerRegistriesPayload(registries={})
        assert isinstance(payload.registries, dict)
