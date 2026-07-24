"""Tests for ai.backend.common.dto.manager.v2.resource_group.response module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentHandlerOptionsInfo,
    DeploymentOptionsInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    CreateResourceGroupPayload,
    DeleteResourceGroupPayload,
    PreemptionConfigInfo,
    ResourceGroupDetailNode,
    ResourceGroupMetadataInfo,
    ResourceGroupNetworkConfigInfo,
    ResourceGroupNode,
    ResourceGroupSchedulerConfigInfo,
    ResourceGroupStatusInfo,
    UpdateResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    PreemptionOrderDTO,
    SchedulerTypeDTO,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.response import (
    DefaultSessionOptionsInfo,
    HandlerOptionsInfo,
    SessionHandlerOptionsInfo,
)
from ai.backend.common.dto.manager.v2.session_options.types import (
    AgentSelectionPolicyEnum,
    FailurePolicyEnum,
)


def _make_resource_group_node(name: str = "test-group") -> ResourceGroupNode:
    return ResourceGroupNode(
        id=uuid.uuid4(),
        name=name,
        domain_name="default",
        description="A test resource group",
        is_active=True,
        total_resource_slots={"cpu": "4", "mem": "8g"},
        allowed_vfolder_hosts={"default": "rw"},
        integration_name=None,
        resource_policy=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        modified_at=datetime(2024, 6, 1, tzinfo=UTC),
    )


def _make_resource_group_detail_node(name: str = "test-group") -> ResourceGroupDetailNode:
    return ResourceGroupDetailNode(
        id=name,
        resource_group_id=uuid.uuid4(),
        name=name,
        status=ResourceGroupStatusInfo(is_active=True, is_public=True),
        metadata=ResourceGroupMetadataInfo(
            description="A test resource group",
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        network=ResourceGroupNetworkConfigInfo(
            wsproxy_addr="http://localhost:10200",
            use_host_network=False,
        ),
        scheduler=ResourceGroupSchedulerConfigInfo(
            type=SchedulerTypeDTO.FIFO,
            preemption=PreemptionConfigInfo(
                enabled=False,
                preemptible_priority=5,
                order=PreemptionOrderDTO.OLDEST,
                mode=PreemptionModeDTO.TERMINATE,
                preemption_min_runtime=0.0,
            ),
        ),
        default_deployment_options=DeploymentOptionsInfo(
            handler_options=DeploymentHandlerOptionsInfo(
                default=HandlerOptionsInfo(timeout_sec=None, max_retry_count=None),
                by_handler=[],
            ),
        ),
        default_session_options=DefaultSessionOptionsInfo(
            priority=0,
            is_preemptible=False,
            cluster_mode=ClusterModeEnum.SINGLE_NODE,
            default_failure_policy=FailurePolicyEnum.STRICT,
            default_kernel_execution_spec=None,
            handler_options=SessionHandlerOptionsInfo(
                default=HandlerOptionsInfo(timeout_sec=None, max_retry_count=None),
                by_handler=[],
            ),
            agent_selection_policy=AgentSelectionPolicyEnum.STRICT,
        ),
    )


class TestResourceGroupNode:
    """Tests for ResourceGroupNode model."""

    def test_valid_creation_with_all_fields(self) -> None:
        node = _make_resource_group_node()
        assert node.name == "test-group"
        assert node.domain_name == "default"
        assert node.is_active is True
        assert node.total_resource_slots == {"cpu": "4", "mem": "8g"}

    def test_valid_creation_with_optional_none(self) -> None:
        node = _make_resource_group_node()
        assert node.description == "A test resource group"
        assert node.integration_name is None
        assert node.resource_policy is None

    def test_serializes_correctly(self) -> None:
        node = _make_resource_group_node()
        data = node.model_dump()
        assert "id" in data
        assert "name" in data
        assert "domain_name" in data
        assert "total_resource_slots" in data
        assert "allowed_vfolder_hosts" in data

    def test_round_trip(self) -> None:
        node = _make_resource_group_node()
        json_data = node.model_dump_json()
        restored = ResourceGroupNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.domain_name == node.domain_name
        assert restored.is_active == node.is_active
        assert restored.id == node.id


class TestCreateResourceGroupPayload:
    """Tests for CreateResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        node = _make_resource_group_detail_node()
        payload = CreateResourceGroupPayload(resource_group=node)
        assert payload.resource_group.name == "test-group"

    def test_round_trip(self) -> None:
        node = _make_resource_group_detail_node()
        payload = CreateResourceGroupPayload(resource_group=node)
        json_data = payload.model_dump_json()
        restored = CreateResourceGroupPayload.model_validate_json(json_data)
        assert restored.resource_group.name == payload.resource_group.name


class TestUpdateResourceGroupPayload:
    """Tests for UpdateResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        node = _make_resource_group_detail_node()
        payload = UpdateResourceGroupPayload(resource_group=node)
        assert payload.resource_group.name == "test-group"

    def test_round_trip(self) -> None:
        node = _make_resource_group_detail_node()
        payload = UpdateResourceGroupPayload(resource_group=node)
        json_data = payload.model_dump_json()
        restored = UpdateResourceGroupPayload.model_validate_json(json_data)
        assert restored.resource_group.name == payload.resource_group.name


class TestDeleteResourceGroupPayload:
    """Tests for DeleteResourceGroupPayload model."""

    def test_valid_creation(self) -> None:
        payload = DeleteResourceGroupPayload(id="test-group")
        assert payload.id == "test-group"

    def test_round_trip(self) -> None:
        payload = DeleteResourceGroupPayload(id="test-group")
        json_data = payload.model_dump_json()
        restored = DeleteResourceGroupPayload.model_validate_json(json_data)
        assert restored.id == payload.id
