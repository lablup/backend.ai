"""Tests for ai.backend.common.dto.manager.v2.scaling_group.response module."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.scaling_group.response import (
    PreemptionConfigInfo,
    ScalingGroupMetadataInfo,
    ScalingGroupNetworkInfo,
    ScalingGroupNode,
    ScalingGroupSchedulerInfo,
    ScalingGroupStatusInfo,
    UpdateScalingGroupPayload,
)
from ai.backend.common.dto.manager.v2.scaling_group.types import (
    PreemptionMode,
    PreemptionOrder,
    SchedulerType,
)


def _make_preemption_config() -> PreemptionConfigInfo:
    return PreemptionConfigInfo(
        preemptible_priority=5,
        order=PreemptionOrder.OLDEST,
        mode=PreemptionMode.TERMINATE,
    )


def _make_scheduler_info() -> ScalingGroupSchedulerInfo:
    return ScalingGroupSchedulerInfo(
        type=SchedulerType.FIFO,
        preemption=_make_preemption_config(),
    )


def _make_scaling_group_node(name: str = "test-sgroup") -> ScalingGroupNode:
    return ScalingGroupNode(
        name=name,
        status=ScalingGroupStatusInfo(is_active=True, is_public=False),
        metadata=ScalingGroupMetadataInfo(
            description="Test scaling group",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        network=ScalingGroupNetworkInfo(wsproxy_addr=None, use_host_network=False),
        scheduler=_make_scheduler_info(),
    )


class TestScalingGroupStatusInfo:
    """Tests for ScalingGroupStatusInfo model."""

    def test_valid_creation(self) -> None:
        info = ScalingGroupStatusInfo(is_active=True, is_public=False)
        assert info.is_active is True
        assert info.is_public is False


class TestScalingGroupMetadataInfo:
    """Tests for ScalingGroupMetadataInfo model."""

    def test_valid_creation_with_description(self) -> None:
        now = datetime(2024, 1, 1, tzinfo=UTC)
        info = ScalingGroupMetadataInfo(description="desc", created_at=now)
        assert info.description == "desc"
        assert info.created_at == now

    def test_valid_creation_without_description(self) -> None:
        now = datetime(2024, 1, 1, tzinfo=UTC)
        info = ScalingGroupMetadataInfo(created_at=now)
        assert info.description is None


class TestScalingGroupNetworkInfo:
    """Tests for ScalingGroupNetworkInfo model."""

    def test_valid_creation_with_proxy(self) -> None:
        info = ScalingGroupNetworkInfo(wsproxy_addr="ws://proxy:8080", use_host_network=True)
        assert info.wsproxy_addr == "ws://proxy:8080"
        assert info.use_host_network is True

    def test_valid_creation_without_proxy(self) -> None:
        info = ScalingGroupNetworkInfo(use_host_network=False)
        assert info.wsproxy_addr is None


class TestPreemptionConfigInfo:
    """Tests for PreemptionConfigInfo model."""

    def test_valid_creation(self) -> None:
        info = _make_preemption_config()
        assert info.preemptible_priority == 5
        assert info.order == PreemptionOrder.OLDEST
        assert info.mode == PreemptionMode.TERMINATE


class TestScalingGroupSchedulerInfo:
    """Tests for ScalingGroupSchedulerInfo model."""

    def test_valid_creation(self) -> None:
        info = _make_scheduler_info()
        assert info.type == SchedulerType.FIFO
        assert info.preemption.preemptible_priority == 5


class TestScalingGroupNode:
    """Tests for ScalingGroupNode model."""

    def test_valid_creation(self) -> None:
        node = _make_scaling_group_node()
        assert node.name == "test-sgroup"
        assert node.status.is_active is True
        assert node.metadata.description == "Test scaling group"
        assert node.network.use_host_network is False
        assert node.scheduler.type == SchedulerType.FIFO

    def test_nested_structure_serializes_correctly(self) -> None:
        node = _make_scaling_group_node()
        data = node.model_dump()
        assert "status" in data
        assert "metadata" in data
        assert "network" in data
        assert "scheduler" in data
        assert data["status"]["is_active"] is True
        assert data["scheduler"]["preemption"]["preemptible_priority"] == 5

    def test_round_trip(self) -> None:
        node = _make_scaling_group_node()
        json_data = node.model_dump_json()
        restored = ScalingGroupNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.status.is_active == node.status.is_active
        assert restored.scheduler.type == node.scheduler.type


class TestUpdateScalingGroupPayload:
    """Tests for UpdateScalingGroupPayload model."""

    def test_valid_creation(self) -> None:
        node = _make_scaling_group_node()
        payload = UpdateScalingGroupPayload(scaling_group=node)
        assert payload.scaling_group.name == "test-sgroup"

    def test_round_trip(self) -> None:
        node = _make_scaling_group_node()
        payload = UpdateScalingGroupPayload(scaling_group=node)
        json_data = payload.model_dump_json()
        restored = UpdateScalingGroupPayload.model_validate_json(json_data)
        assert restored.scaling_group.name == payload.scaling_group.name
