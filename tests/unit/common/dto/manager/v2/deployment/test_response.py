"""Tests for ai.backend.common.dto.manager.v2.deployment.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    ActivateDeploymentPayload,
    AddRevisionPayload,
    CreateDeploymentPayload,
    DeleteDeploymentPayload,
    DeploymentNode,
    ExtraVFolderMountNode,
    RevisionNode,
    RouteNode,
    ScaleDeploymentPayload,
    UpdateDeploymentPayload,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenConfigInfo,
    DeploymentBasicInfo,
    DeploymentPolicyInfo,
    DeploymentRevisionInfo,
    NetworkConfigInfo,
    ReplicaStateInfo,
    RollingUpdateConfigInfo,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant


def _make_basic_info(**kwargs: object) -> DeploymentBasicInfo:
    defaults: dict[str, Any] = {
        "name": "test-deployment",
        "status": ModelDeploymentStatus.READY,
        "tags": [],
        "project_id": uuid.uuid4(),
        "domain_name": "default",
        "created_user_id": uuid.uuid4(),
    }
    defaults.update(kwargs)
    return DeploymentBasicInfo(**defaults)


def _make_network_info(**kwargs: object) -> NetworkConfigInfo:
    defaults: dict[str, Any] = {
        "open_to_public": False,
        "url": None,
        "preferred_domain_name": None,
    }
    defaults.update(kwargs)
    return NetworkConfigInfo(**defaults)


def _make_replica_state(**kwargs: object) -> ReplicaStateInfo:
    defaults: dict[str, Any] = {
        "desired_replica_count": 2,
        "replica_ids": [],
    }
    defaults.update(kwargs)
    return ReplicaStateInfo(**defaults)


def _make_revision_info(**kwargs: object) -> DeploymentRevisionInfo:
    defaults: dict[str, Any] = {
        "cluster_mode": ClusterMode.SINGLE_NODE,
        "cluster_size": 1,
        "resource_group": "default",
        "resource_slots": {"cpu": "2"},
        "image_id": uuid.uuid4(),
        "runtime_variant": RuntimeVariant.CUSTOM,
        "model_vfolder_id": None,
        "model_mount_destination": None,
        "model_definition_path": None,
    }
    defaults.update(kwargs)
    return DeploymentRevisionInfo(**defaults)


def _make_revision_node(**kwargs: object) -> RevisionNode:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "name": "v1",
        "revision_info": _make_revision_info(),
        "created_at": datetime.now(tz=UTC),
        "extra_mounts": [],
    }
    defaults.update(kwargs)
    return RevisionNode(**defaults)


def _make_deployment_node(**kwargs: object) -> DeploymentNode:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "basic": _make_basic_info(),
        "network": _make_network_info(),
        "replica_state": _make_replica_state(),
        "default_deployment_strategy": DeploymentStrategy.ROLLING,
        "current_revision": None,
        "policy": None,
        "created_at": datetime.now(tz=UTC),
        "updated_at": datetime.now(tz=UTC),
    }
    defaults.update(kwargs)
    return DeploymentNode(**defaults)


class TestExtraVFolderMountNode:
    """Tests for ExtraVFolderMountNode model."""

    def test_valid_creation(self) -> None:
        vfolder_id = uuid.uuid4()
        node = ExtraVFolderMountNode(vfolder_id=vfolder_id, mount_destination="/data")
        assert node.vfolder_id == vfolder_id
        assert node.mount_destination == "/data"

    def test_mount_destination_defaults_to_none(self) -> None:
        node = ExtraVFolderMountNode(vfolder_id=uuid.uuid4())
        assert node.mount_destination is None

    def test_round_trip(self) -> None:
        vfolder_id = uuid.uuid4()
        node = ExtraVFolderMountNode(vfolder_id=vfolder_id, mount_destination="/data")
        json_str = node.model_dump_json()
        restored = ExtraVFolderMountNode.model_validate_json(json_str)
        assert restored.vfolder_id == vfolder_id
        assert restored.mount_destination == "/data"


class TestRevisionNode:
    """Tests for RevisionNode model."""

    def test_creation_with_all_fields(self) -> None:
        revision_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        info = _make_revision_info(image_id=uuid.uuid4())
        node = RevisionNode(
            id=revision_id,
            name="v1",
            revision_info=info,
            created_at=now,
            extra_mounts=[],
        )
        assert node.id == revision_id
        assert node.name == "v1"
        assert node.created_at == now
        assert node.extra_mounts == []

    def test_extra_mounts_defaults_to_empty_list(self) -> None:
        node = RevisionNode(
            id=uuid.uuid4(),
            name="v1",
            revision_info=_make_revision_info(),
            created_at=datetime.now(tz=UTC),
        )
        assert node.extra_mounts == []

    def test_with_extra_mounts(self) -> None:
        mount = ExtraVFolderMountNode(vfolder_id=uuid.uuid4(), mount_destination="/data")
        node = _make_revision_node(extra_mounts=[mount])
        assert len(node.extra_mounts) == 1
        assert node.extra_mounts[0].mount_destination == "/data"

    def test_round_trip(self) -> None:
        revision_id = uuid.uuid4()
        node = _make_revision_node(id=revision_id, name="v2")
        json_str = node.model_dump_json()
        restored = RevisionNode.model_validate_json(json_str)
        assert restored.id == revision_id
        assert restored.name == "v2"


class TestDeploymentNode:
    """Tests for DeploymentNode model."""

    def test_creation_with_required_fields(self) -> None:
        deployment_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = DeploymentNode(
            id=deployment_id,
            basic=_make_basic_info(),
            network=_make_network_info(),
            replica_state=_make_replica_state(),
            default_deployment_strategy=DeploymentStrategy.ROLLING,
            created_at=now,
            updated_at=now,
        )
        assert node.id == deployment_id
        assert node.current_revision is None
        assert node.policy is None

    def test_current_revision_defaults_to_none(self) -> None:
        node = _make_deployment_node()
        assert node.current_revision is None

    def test_policy_defaults_to_none(self) -> None:
        node = _make_deployment_node()
        assert node.policy is None

    def test_with_current_revision(self) -> None:
        rev = _make_revision_node()
        node = _make_deployment_node(current_revision=rev)
        assert node.current_revision is not None
        assert node.current_revision.name == "v1"

    def test_with_rolling_policy(self) -> None:
        rolling = RollingUpdateConfigInfo(max_surge=1, max_unavailable=0)
        policy = DeploymentPolicyInfo(
            strategy=DeploymentStrategy.ROLLING,
            rollback_on_failure=True,
            rolling_update=rolling,
            blue_green=None,
        )
        node = _make_deployment_node(policy=policy)
        assert node.policy is not None
        assert node.policy.strategy == DeploymentStrategy.ROLLING
        assert node.policy.rolling_update is not None

    def test_with_blue_green_policy(self) -> None:
        bg = BlueGreenConfigInfo(auto_promote=False, promote_delay_seconds=0)
        policy = DeploymentPolicyInfo(
            strategy=DeploymentStrategy.BLUE_GREEN,
            rollback_on_failure=False,
            rolling_update=None,
            blue_green=bg,
        )
        node = _make_deployment_node(policy=policy)
        assert node.policy is not None
        assert node.policy.strategy == DeploymentStrategy.BLUE_GREEN

    def test_basic_info_accessible(self) -> None:
        project_id = uuid.uuid4()
        basic = _make_basic_info(project_id=project_id, name="my-deploy")
        node = _make_deployment_node(basic=basic)
        assert node.basic.name == "my-deploy"
        assert node.basic.project_id == project_id

    def test_network_info_accessible(self) -> None:
        network = _make_network_info(open_to_public=True, url="https://example.com")
        node = _make_deployment_node(network=network)
        assert node.network.open_to_public is True
        assert node.network.url == "https://example.com"

    def test_replica_state_accessible(self) -> None:
        replica_ids = [uuid.uuid4(), uuid.uuid4()]
        replica_state = _make_replica_state(desired_replica_count=2, replica_ids=replica_ids)
        node = _make_deployment_node(replica_state=replica_state)
        assert node.replica_state.desired_replica_count == 2
        assert len(node.replica_state.replica_ids) == 2

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        json_str = node.model_dump_json()
        restored = DeploymentNode.model_validate_json(json_str)
        assert restored.id == deployment_id
        assert restored.basic.name == "test-deployment"
        assert restored.current_revision is None

    def test_round_trip_with_revision(self) -> None:
        deployment_id = uuid.uuid4()
        rev = _make_revision_node()
        node = _make_deployment_node(id=deployment_id, current_revision=rev)
        json_str = node.model_dump_json()
        restored = DeploymentNode.model_validate_json(json_str)
        assert restored.id == deployment_id
        assert restored.current_revision is not None
        assert restored.current_revision.name == "v1"

    def test_strategy_is_serialized_as_string(self) -> None:
        node = _make_deployment_node()
        data = json.loads(node.model_dump_json())
        assert isinstance(data["default_deployment_strategy"], str)


class TestRouteNode:
    """Tests for RouteNode model."""

    def test_creation_with_all_fields(self) -> None:
        route_id = uuid.uuid4()
        endpoint_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RouteNode(
            id=route_id,
            endpoint_id=endpoint_id,
            session_id=None,
            status=RouteStatus.HEALTHY,
            traffic_ratio=0.5,
            created_at=now,
            revision_id=None,
            traffic_status=RouteTrafficStatus.ACTIVE,
            error_data={},
        )
        assert node.id == route_id
        assert node.endpoint_id == endpoint_id
        assert node.status == RouteStatus.HEALTHY
        assert node.traffic_ratio == 0.5
        assert node.traffic_status == RouteTrafficStatus.ACTIVE

    def test_session_id_defaults_to_none(self) -> None:
        node = RouteNode(
            id=uuid.uuid4(),
            endpoint_id=uuid.uuid4(),
            status=RouteStatus.PROVISIONING,
            traffic_ratio=1.0,
            created_at=datetime.now(tz=UTC),
            traffic_status=RouteTrafficStatus.INACTIVE,
        )
        assert node.session_id is None

    def test_revision_id_defaults_to_none(self) -> None:
        node = RouteNode(
            id=uuid.uuid4(),
            endpoint_id=uuid.uuid4(),
            status=RouteStatus.HEALTHY,
            traffic_ratio=1.0,
            created_at=datetime.now(tz=UTC),
            traffic_status=RouteTrafficStatus.ACTIVE,
        )
        assert node.revision_id is None

    def test_error_data_defaults_to_empty_dict(self) -> None:
        node = RouteNode(
            id=uuid.uuid4(),
            endpoint_id=uuid.uuid4(),
            status=RouteStatus.HEALTHY,
            traffic_ratio=1.0,
            created_at=datetime.now(tz=UTC),
            traffic_status=RouteTrafficStatus.ACTIVE,
        )
        assert node.error_data == {}

    def test_round_trip(self) -> None:
        route_id = uuid.uuid4()
        endpoint_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RouteNode(
            id=route_id,
            endpoint_id=endpoint_id,
            status=RouteStatus.HEALTHY,
            traffic_ratio=0.5,
            created_at=now,
            traffic_status=RouteTrafficStatus.ACTIVE,
            error_data={"message": "ok"},
        )
        json_str = node.model_dump_json()
        restored = RouteNode.model_validate_json(json_str)
        assert restored.id == route_id
        assert restored.endpoint_id == endpoint_id
        assert restored.status == RouteStatus.HEALTHY
        assert restored.traffic_ratio == 0.5
        assert restored.error_data == {"message": "ok"}


class TestCreateDeploymentPayload:
    """Tests for CreateDeploymentPayload model."""

    def test_creation_with_deployment_node(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = CreateDeploymentPayload(deployment=node)
        assert payload.deployment.id == deployment_id

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = CreateDeploymentPayload(deployment=node)
        json_str = payload.model_dump_json()
        restored = CreateDeploymentPayload.model_validate_json(json_str)
        assert restored.deployment.id == deployment_id


class TestUpdateDeploymentPayload:
    """Tests for UpdateDeploymentPayload model."""

    def test_creation_with_deployment_node(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = UpdateDeploymentPayload(deployment=node)
        assert payload.deployment.id == deployment_id

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = UpdateDeploymentPayload(deployment=node)
        json_str = payload.model_dump_json()
        restored = UpdateDeploymentPayload.model_validate_json(json_str)
        assert restored.deployment.id == deployment_id


class TestDeleteDeploymentPayload:
    """Tests for DeleteDeploymentPayload model."""

    def test_creation_with_uuid(self) -> None:
        deployment_id = uuid.uuid4()
        payload = DeleteDeploymentPayload(id=deployment_id)
        assert payload.id == deployment_id

    def test_id_is_uuid_instance(self) -> None:
        deployment_id = uuid.uuid4()
        payload = DeleteDeploymentPayload(id=deployment_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        payload = DeleteDeploymentPayload(id=deployment_id)
        json_str = payload.model_dump_json()
        restored = DeleteDeploymentPayload.model_validate_json(json_str)
        assert restored.id == deployment_id


class TestActivateDeploymentPayload:
    """Tests for ActivateDeploymentPayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = ActivateDeploymentPayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = ActivateDeploymentPayload(success=False)
        assert payload.success is False

    def test_round_trip(self) -> None:
        payload = ActivateDeploymentPayload(success=True)
        json_str = payload.model_dump_json()
        restored = ActivateDeploymentPayload.model_validate_json(json_str)
        assert restored.success is True


class TestScaleDeploymentPayload:
    """Tests for ScaleDeploymentPayload model."""

    def test_creation_with_deployment_node(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = ScaleDeploymentPayload(deployment=node)
        assert payload.deployment.id == deployment_id

    def test_round_trip(self) -> None:
        deployment_id = uuid.uuid4()
        node = _make_deployment_node(id=deployment_id)
        payload = ScaleDeploymentPayload(deployment=node)
        json_str = payload.model_dump_json()
        restored = ScaleDeploymentPayload.model_validate_json(json_str)
        assert restored.deployment.id == deployment_id


class TestAddRevisionPayload:
    """Tests for AddRevisionPayload model."""

    def test_creation_with_revision_node(self) -> None:
        revision_id = uuid.uuid4()
        rev = _make_revision_node(id=revision_id, name="v2")
        payload = AddRevisionPayload(revision=rev)
        assert payload.revision.id == revision_id
        assert payload.revision.name == "v2"

    def test_round_trip(self) -> None:
        revision_id = uuid.uuid4()
        rev = _make_revision_node(id=revision_id, name="v2")
        payload = AddRevisionPayload(revision=rev)
        json_str = payload.model_dump_json()
        restored = AddRevisionPayload.model_validate_json(json_str)
        assert restored.revision.id == revision_id
        assert restored.revision.name == "v2"
