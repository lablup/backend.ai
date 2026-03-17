"""Tests for ai.backend.common.dto.manager.v2.agent.response module."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.agent.response import (
    AgentNetworkInfo,
    AgentNode,
    AgentResourceInfo,
    AgentResourceStatsPayload,
    AgentStatusInfo,
    AgentSystemInfo,
    GetAgentDetailPayload,
    SearchAgentsPayload,
)


def _make_resource_info() -> AgentResourceInfo:
    return AgentResourceInfo(
        capacity={"cpu": "16", "mem": "64g"},
        used={"cpu": "4", "mem": "16g"},
        free={"cpu": "12", "mem": "48g"},
    )


def _make_status_info(status: str = "ALIVE") -> AgentStatusInfo:
    return AgentStatusInfo(status=status, schedulable=True)


def _make_system_info() -> AgentSystemInfo:
    return AgentSystemInfo(architecture="x86_64", version="26.1.0")


def _make_network_info() -> AgentNetworkInfo:
    return AgentNetworkInfo(region="us-east-1", addr="192.168.1.100:6001")


def _make_agent_node(agent_id: str = "agent-001") -> AgentNode:
    return AgentNode(
        id=agent_id,
        resource_info=_make_resource_info(),
        status_info=_make_status_info(),
        system_info=_make_system_info(),
        network_info=_make_network_info(),
    )


class TestAgentResourceInfo:
    """Tests for AgentResourceInfo model."""

    def test_creation_with_all_fields(self) -> None:
        info = AgentResourceInfo(
            capacity={"cpu": "16", "mem": "64g"},
            used={"cpu": "4", "mem": "16g"},
            free={"cpu": "12", "mem": "48g"},
        )
        assert info.capacity == {"cpu": "16", "mem": "64g"}
        assert info.used == {"cpu": "4", "mem": "16g"}
        assert info.free == {"cpu": "12", "mem": "48g"}

    def test_round_trip(self) -> None:
        info = _make_resource_info()
        json_str = info.model_dump_json()
        restored = AgentResourceInfo.model_validate_json(json_str)
        assert restored.capacity == info.capacity
        assert restored.used == info.used
        assert restored.free == info.free

    def test_json_structure(self) -> None:
        info = _make_resource_info()
        data = json.loads(info.model_dump_json())
        assert "capacity" in data
        assert "used" in data
        assert "free" in data
        assert isinstance(data["capacity"], dict)


class TestAgentStatusInfo:
    """Tests for AgentStatusInfo model."""

    def test_creation_with_required_fields(self) -> None:
        info = AgentStatusInfo(status="ALIVE", schedulable=True)
        assert info.status == "ALIVE"
        assert info.schedulable is True
        assert info.status_changed is None
        assert info.first_contact is None
        assert info.lost_at is None

    def test_not_schedulable(self) -> None:
        info = AgentStatusInfo(status="LOST", schedulable=False)
        assert info.schedulable is False

    def test_with_timestamps(self) -> None:
        now = datetime.now(tz=UTC)
        info = AgentStatusInfo(
            status="ALIVE",
            schedulable=True,
            status_changed=now,
            first_contact=now,
        )
        assert info.status_changed == now
        assert info.first_contact == now

    def test_with_lost_at(self) -> None:
        now = datetime.now(tz=UTC)
        info = AgentStatusInfo(
            status="LOST",
            schedulable=False,
            lost_at=now,
        )
        assert info.lost_at == now

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = AgentStatusInfo(
            status="ALIVE",
            schedulable=True,
            status_changed=now,
            first_contact=now,
        )
        json_str = info.model_dump_json()
        restored = AgentStatusInfo.model_validate_json(json_str)
        assert restored.status == "ALIVE"
        assert restored.schedulable is True
        assert restored.status_changed is not None


class TestAgentSystemInfo:
    """Tests for AgentSystemInfo model."""

    def test_creation_with_required_fields(self) -> None:
        info = AgentSystemInfo(architecture="x86_64", version="26.1.0")
        assert info.architecture == "x86_64"
        assert info.version == "26.1.0"
        assert info.compute_plugins is None

    def test_with_compute_plugins(self) -> None:
        plugins = {"cuda": {"version": "12.0"}, "rocm": {"version": "5.0"}}
        info = AgentSystemInfo(
            architecture="x86_64",
            version="26.1.0",
            compute_plugins=plugins,
        )
        assert info.compute_plugins == plugins
        assert info.compute_plugins["cuda"]["version"] == "12.0"

    def test_aarch64_architecture(self) -> None:
        info = AgentSystemInfo(architecture="aarch64", version="26.0.0")
        assert info.architecture == "aarch64"

    def test_round_trip(self) -> None:
        info = AgentSystemInfo(
            architecture="x86_64",
            version="26.1.0",
            compute_plugins={"cuda": {"version": "12.0"}},
        )
        json_str = info.model_dump_json()
        restored = AgentSystemInfo.model_validate_json(json_str)
        assert restored.architecture == "x86_64"
        assert restored.version == "26.1.0"
        assert restored.compute_plugins is not None
        assert restored.compute_plugins["cuda"]["version"] == "12.0"


class TestAgentNetworkInfo:
    """Tests for AgentNetworkInfo model."""

    def test_creation_with_all_fields(self) -> None:
        info = AgentNetworkInfo(region="us-east-1", addr="192.168.1.100:6001")
        assert info.region == "us-east-1"
        assert info.addr == "192.168.1.100:6001"

    def test_round_trip(self) -> None:
        info = _make_network_info()
        json_str = info.model_dump_json()
        restored = AgentNetworkInfo.model_validate_json(json_str)
        assert restored.region == info.region
        assert restored.addr == info.addr


class TestAgentNode:
    """Tests for AgentNode model with all 4 nested sub-models."""

    def test_creation_with_all_nested(self) -> None:
        node = _make_agent_node()
        assert node.id == "agent-001"
        assert node.resource_info is not None
        assert node.status_info is not None
        assert node.system_info is not None
        assert node.network_info is not None

    def test_nested_values_accessible(self) -> None:
        node = _make_agent_node()
        assert node.resource_info.capacity["cpu"] == "16"
        assert node.status_info.status == "ALIVE"
        assert node.system_info.architecture == "x86_64"
        assert node.network_info.region == "us-east-1"

    def test_serializes_to_json(self) -> None:
        node = _make_agent_node()
        data = json.loads(node.model_dump_json())
        assert "id" in data
        assert "resource_info" in data
        assert "status_info" in data
        assert "system_info" in data
        assert "network_info" in data

    def test_nested_json_structure(self) -> None:
        node = _make_agent_node()
        data = json.loads(node.model_dump_json())
        assert isinstance(data["resource_info"], dict)
        assert "capacity" in data["resource_info"]
        assert isinstance(data["status_info"], dict)
        assert "status" in data["status_info"]

    def test_round_trip(self) -> None:
        node = _make_agent_node("agent-xyz")
        json_str = node.model_dump_json()
        restored = AgentNode.model_validate_json(json_str)
        assert restored.id == "agent-xyz"
        assert restored.resource_info.capacity == node.resource_info.capacity
        assert restored.status_info.status == node.status_info.status
        assert restored.system_info.architecture == node.system_info.architecture
        assert restored.network_info.region == node.network_info.region


class TestGetAgentDetailPayload:
    """Tests for GetAgentDetailPayload model."""

    def test_creation_with_agent_node(self) -> None:
        node = _make_agent_node()
        payload = GetAgentDetailPayload(agent=node)
        assert payload.agent.id == "agent-001"

    def test_nested_values_accessible(self) -> None:
        node = _make_agent_node("test-agent")
        payload = GetAgentDetailPayload(agent=node)
        assert payload.agent.resource_info.capacity["cpu"] == "16"
        assert payload.agent.status_info.schedulable is True

    def test_round_trip(self) -> None:
        node = _make_agent_node("my-agent")
        payload = GetAgentDetailPayload(agent=node)
        json_str = payload.model_dump_json()
        restored = GetAgentDetailPayload.model_validate_json(json_str)
        assert restored.agent.id == "my-agent"
        assert restored.agent.status_info.status == "ALIVE"


class TestSearchAgentsPayload:
    """Tests for SearchAgentsPayload model."""

    def test_creation_with_empty_items(self) -> None:
        pagination = PaginationInfo(total=0, offset=0, limit=20)
        payload = SearchAgentsPayload(items=[], pagination=pagination)
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_creation_with_items(self) -> None:
        node = _make_agent_node()
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchAgentsPayload(items=[node], pagination=pagination)
        assert len(payload.items) == 1
        assert payload.items[0].id == "agent-001"

    def test_nested_json_structure(self) -> None:
        node = _make_agent_node()
        pagination = PaginationInfo(total=1, offset=0, limit=20)
        payload = SearchAgentsPayload(items=[node], pagination=pagination)
        data = json.loads(payload.model_dump_json())
        assert "items" in data
        assert "pagination" in data
        assert isinstance(data["items"], list)
        assert "resource_info" in data["items"][0]

    def test_round_trip(self) -> None:
        nodes = [_make_agent_node(f"agent-{i}") for i in range(3)]
        pagination = PaginationInfo(total=3, offset=0, limit=10)
        payload = SearchAgentsPayload(items=nodes, pagination=pagination)
        json_str = payload.model_dump_json()
        restored = SearchAgentsPayload.model_validate_json(json_str)
        assert len(restored.items) == 3
        assert restored.pagination.total == 3
        assert restored.pagination.limit == 10


class TestAgentResourceStatsPayload:
    """Tests for AgentResourceStatsPayload model."""

    def test_creation_with_slot_dicts(self) -> None:
        payload = AgentResourceStatsPayload(
            total_used_slots={"cpu": "8", "mem": "32g"},
            total_free_slots={"cpu": "24", "mem": "96g"},
            total_capacity_slots={"cpu": "32", "mem": "128g"},
        )
        assert payload.total_used_slots == {"cpu": "8", "mem": "32g"}
        assert payload.total_free_slots == {"cpu": "24", "mem": "96g"}
        assert payload.total_capacity_slots == {"cpu": "32", "mem": "128g"}

    def test_json_structure(self) -> None:
        payload = AgentResourceStatsPayload(
            total_used_slots={"cpu": "4"},
            total_free_slots={"cpu": "12"},
            total_capacity_slots={"cpu": "16"},
        )
        data = json.loads(payload.model_dump_json())
        assert "total_used_slots" in data
        assert "total_free_slots" in data
        assert "total_capacity_slots" in data
        assert data["total_capacity_slots"]["cpu"] == "16"

    def test_round_trip(self) -> None:
        payload = AgentResourceStatsPayload(
            total_used_slots={"cpu": "8", "mem": "32g", "cuda.devices": "2"},
            total_free_slots={"cpu": "24", "mem": "96g", "cuda.devices": "6"},
            total_capacity_slots={"cpu": "32", "mem": "128g", "cuda.devices": "8"},
        )
        json_str = payload.model_dump_json()
        restored = AgentResourceStatsPayload.model_validate_json(json_str)
        assert restored.total_used_slots == payload.total_used_slots
        assert restored.total_free_slots == payload.total_free_slots
        assert restored.total_capacity_slots == payload.total_capacity_slots
