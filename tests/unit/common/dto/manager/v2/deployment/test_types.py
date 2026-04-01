"""Tests for ai.backend.common.dto.manager.v2.deployment.types module."""

from __future__ import annotations

import json
import uuid

from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenConfigInfo,
    DeploymentBasicInfo,
    DeploymentOrderField,
    DeploymentPolicyInfo,
    DeploymentRevisionInfo,
    IntOrPercent,
    NetworkConfigInfo,
    OrderDirection,
    ReplicaStateInfo,
    RevisionOrderField,
    RollingUpdateConfigInfo,
    RouteOrderField,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentStrategy as ExportedDeploymentStrategy,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    ModelDeploymentStatus as ExportedModelDeploymentStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    RouteStatus as ExportedRouteStatus,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    RouteTrafficStatus as ExportedRouteTrafficStatus,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestDeploymentOrderField:
    """Tests for DeploymentOrderField enum."""

    def test_name_value(self) -> None:
        assert DeploymentOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert DeploymentOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert DeploymentOrderField.UPDATED_AT.value == "updated_at"

    def test_enum_members_count(self) -> None:
        members = list(DeploymentOrderField)
        assert len(members) == 3

    def test_all_values_are_strings(self) -> None:
        for member in DeploymentOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert DeploymentOrderField("name") is DeploymentOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert DeploymentOrderField("created_at") is DeploymentOrderField.CREATED_AT

    def test_from_string_updated_at(self) -> None:
        assert DeploymentOrderField("updated_at") is DeploymentOrderField.UPDATED_AT


class TestRevisionOrderField:
    """Tests for RevisionOrderField enum."""

    def test_name_value(self) -> None:
        assert RevisionOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert RevisionOrderField.CREATED_AT.value == "created_at"

    def test_enum_members_count(self) -> None:
        members = list(RevisionOrderField)
        assert len(members) == 2

    def test_all_values_are_strings(self) -> None:
        for member in RevisionOrderField:
            assert isinstance(member.value, str)


class TestRouteOrderField:
    """Tests for RouteOrderField enum."""

    def test_created_at_value(self) -> None:
        assert RouteOrderField.CREATED_AT.value == "created_at"

    def test_status_value(self) -> None:
        assert RouteOrderField.STATUS.value == "status"

    def test_traffic_ratio_value(self) -> None:
        assert RouteOrderField.TRAFFIC_RATIO.value == "traffic_ratio"

    def test_enum_members_count(self) -> None:
        members = list(RouteOrderField)
        assert len(members) == 3

    def test_all_values_are_strings(self) -> None:
        for member in RouteOrderField:
            assert isinstance(member.value, str)


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_model_deployment_status_is_same_object(self) -> None:
        assert ExportedModelDeploymentStatus is ModelDeploymentStatus

    def test_deployment_strategy_is_same_object(self) -> None:
        assert ExportedDeploymentStrategy is DeploymentStrategy

    def test_route_status_is_same_object(self) -> None:
        assert ExportedRouteStatus is RouteStatus

    def test_route_traffic_status_is_same_object(self) -> None:
        assert ExportedRouteTrafficStatus is RouteTrafficStatus

    def test_model_deployment_status_ready_value(self) -> None:
        assert ExportedModelDeploymentStatus.READY.value == "READY"

    def test_deployment_strategy_rolling_value(self) -> None:
        assert ExportedDeploymentStrategy.ROLLING.value == "ROLLING"

    def test_route_status_healthy_value(self) -> None:
        assert ExportedRouteStatus.HEALTHY.value == "healthy"

    def test_route_traffic_status_active_value(self) -> None:
        assert ExportedRouteTrafficStatus.ACTIVE.value == "active"


class TestDeploymentBasicInfo:
    """Tests for DeploymentBasicInfo model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()
        info = DeploymentBasicInfo(
            name="my-deployment",
            status=ModelDeploymentStatus.READY,
            tags=["tag1", "tag2"],
            project_id=project_id,
            domain_name="default",
            created_user_id=user_id,
        )
        assert info.name == "my-deployment"
        assert info.status == ModelDeploymentStatus.READY
        assert info.tags == ["tag1", "tag2"]
        assert info.project_id == project_id
        assert info.domain_name == "default"
        assert info.created_user_id == user_id

    def test_creation_with_empty_tags(self) -> None:
        info = DeploymentBasicInfo(
            name="my-deployment",
            status=ModelDeploymentStatus.PENDING,
            tags=[],
            project_id=uuid.uuid4(),
            domain_name="default",
            created_user_id=uuid.uuid4(),
        )
        assert info.tags == []

    def test_serialization_round_trip(self) -> None:
        project_id = uuid.uuid4()
        user_id = uuid.uuid4()
        info = DeploymentBasicInfo(
            name="my-deployment",
            status=ModelDeploymentStatus.READY,
            tags=["tag1"],
            project_id=project_id,
            domain_name="default",
            created_user_id=user_id,
        )
        json_str = info.model_dump_json()
        restored = DeploymentBasicInfo.model_validate_json(json_str)
        assert restored.name == info.name
        assert restored.status == info.status
        assert restored.tags == info.tags
        assert restored.project_id == info.project_id
        assert restored.domain_name == info.domain_name
        assert restored.created_user_id == info.created_user_id

    def test_model_dump_json_status_is_string(self) -> None:
        info = DeploymentBasicInfo(
            name="test",
            status=ModelDeploymentStatus.SCALING,
            tags=[],
            project_id=uuid.uuid4(),
            domain_name="default",
            created_user_id=uuid.uuid4(),
        )
        data = json.loads(info.model_dump_json())
        assert isinstance(data["status"], str)


class TestNetworkConfigInfo:
    """Tests for NetworkConfigInfo model creation and serialization."""

    def test_creation_with_public_url(self) -> None:
        info = NetworkConfigInfo(
            open_to_public=True,
            url="https://example.com/api",
            preferred_domain_name="example.com",
        )
        assert info.open_to_public is True
        assert info.url == "https://example.com/api"
        assert info.preferred_domain_name == "example.com"

    def test_creation_private_no_url(self) -> None:
        info = NetworkConfigInfo(
            open_to_public=False,
            url=None,
            preferred_domain_name=None,
        )
        assert info.open_to_public is False
        assert info.url is None
        assert info.preferred_domain_name is None

    def test_serialization_round_trip(self) -> None:
        info = NetworkConfigInfo(
            open_to_public=True,
            url="https://example.com",
            preferred_domain_name=None,
        )
        json_str = info.model_dump_json()
        restored = NetworkConfigInfo.model_validate_json(json_str)
        assert restored.open_to_public == info.open_to_public
        assert restored.url == info.url
        assert restored.preferred_domain_name is None


class TestReplicaStateInfo:
    """Tests for ReplicaStateInfo model creation and serialization."""

    def test_creation_with_replicas(self) -> None:
        replica_ids = [uuid.uuid4(), uuid.uuid4()]
        info = ReplicaStateInfo(
            desired_replica_count=2,
            replica_ids=replica_ids,
        )
        assert info.desired_replica_count == 2
        assert info.replica_ids == replica_ids

    def test_creation_with_zero_replicas(self) -> None:
        info = ReplicaStateInfo(
            desired_replica_count=0,
            replica_ids=[],
        )
        assert info.desired_replica_count == 0
        assert info.replica_ids == []

    def test_serialization_round_trip(self) -> None:
        replica_ids = [uuid.uuid4(), uuid.uuid4()]
        info = ReplicaStateInfo(
            desired_replica_count=2,
            replica_ids=replica_ids,
        )
        json_str = info.model_dump_json()
        restored = ReplicaStateInfo.model_validate_json(json_str)
        assert restored.desired_replica_count == info.desired_replica_count
        assert restored.replica_ids == info.replica_ids


class TestDeploymentRevisionInfo:
    """Tests for DeploymentRevisionInfo model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        image_id = uuid.uuid4()
        model_vfolder_id = uuid.uuid4()
        info = DeploymentRevisionInfo(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            resource_group="default",
            resource_slots={"cpu": "2", "mem": "4g"},
            image_id=image_id,
            runtime_variant=RuntimeVariant.CUSTOM,
            model_vfolder_id=model_vfolder_id,
            model_mount_destination="/models",
            model_definition_path="/models/model.yaml",
        )
        assert info.cluster_mode == ClusterMode.SINGLE_NODE
        assert info.cluster_size == 1
        assert info.resource_group == "default"
        assert info.image_id == image_id
        assert info.runtime_variant == RuntimeVariant.CUSTOM
        assert info.model_vfolder_id == model_vfolder_id
        assert info.model_mount_destination == "/models"
        assert info.model_definition_path == "/models/model.yaml"

    def test_creation_with_optional_none(self) -> None:
        info = DeploymentRevisionInfo(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            resource_group="default",
            resource_slots={},
            image_id=uuid.uuid4(),
            runtime_variant=RuntimeVariant.VLLM,
            model_vfolder_id=None,
            model_mount_destination=None,
            model_definition_path=None,
        )
        assert info.model_vfolder_id is None
        assert info.model_mount_destination is None
        assert info.model_definition_path is None

    def test_serialization_round_trip(self) -> None:
        image_id = uuid.uuid4()
        model_id = uuid.uuid4()
        info = DeploymentRevisionInfo(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=2,
            resource_group="gpu-group",
            resource_slots={"cpu": "4", "cuda.shares": "1"},
            image_id=image_id,
            runtime_variant=RuntimeVariant.CUSTOM,
            model_vfolder_id=model_id,
            model_mount_destination="/models",
            model_definition_path="/models/def.yaml",
        )
        json_str = info.model_dump_json()
        restored = DeploymentRevisionInfo.model_validate_json(json_str)
        assert restored.cluster_mode == info.cluster_mode
        assert restored.cluster_size == info.cluster_size
        assert restored.image_id == info.image_id
        assert restored.model_vfolder_id == info.model_vfolder_id


class TestRollingUpdateConfigInfo:
    """Tests for RollingUpdateConfigInfo model creation."""

    def test_creation(self) -> None:
        info = RollingUpdateConfigInfo(
            max_surge=IntOrPercent(count=2),
            max_unavailable=IntOrPercent(count=1),
        )
        assert info.max_surge.count == 2
        assert info.max_unavailable.count == 1

    def test_serialization_round_trip(self) -> None:
        info = RollingUpdateConfigInfo(
            max_surge=IntOrPercent(count=1),
            max_unavailable=IntOrPercent(count=0),
        )
        json_str = info.model_dump_json()
        restored = RollingUpdateConfigInfo.model_validate_json(json_str)
        assert restored.max_surge == info.max_surge
        assert restored.max_unavailable == info.max_unavailable


class TestBlueGreenConfigInfo:
    """Tests for BlueGreenConfigInfo model creation."""

    def test_creation(self) -> None:
        info = BlueGreenConfigInfo(auto_promote=True, promote_delay_seconds=60)
        assert info.auto_promote is True
        assert info.promote_delay_seconds == 60

    def test_serialization_round_trip(self) -> None:
        info = BlueGreenConfigInfo(auto_promote=False, promote_delay_seconds=0)
        json_str = info.model_dump_json()
        restored = BlueGreenConfigInfo.model_validate_json(json_str)
        assert restored.auto_promote == info.auto_promote
        assert restored.promote_delay_seconds == info.promote_delay_seconds


class TestDeploymentPolicyInfo:
    """Tests for DeploymentPolicyInfo model creation and serialization."""

    def test_creation_with_rolling_strategy(self) -> None:
        rolling = RollingUpdateConfigInfo(
            max_surge=IntOrPercent(count=1),
            max_unavailable=IntOrPercent(count=0),
        )
        info = DeploymentPolicyInfo(
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=rolling,
            blue_green=None,
        )
        assert info.strategy == DeploymentStrategy.ROLLING
        assert info.rolling_update is not None
        assert info.rolling_update.max_surge.count == 1
        assert info.blue_green is None

    def test_creation_with_blue_green_strategy(self) -> None:
        bg = BlueGreenConfigInfo(auto_promote=True, promote_delay_seconds=30)
        info = DeploymentPolicyInfo(
            strategy=DeploymentStrategy.BLUE_GREEN,
            rolling_update=None,
            blue_green=bg,
        )
        assert info.strategy == DeploymentStrategy.BLUE_GREEN
        assert info.blue_green is not None
        assert info.blue_green.auto_promote is True

    def test_serialization_round_trip(self) -> None:
        rolling = RollingUpdateConfigInfo(
            max_surge=IntOrPercent(count=2),
            max_unavailable=IntOrPercent(count=1),
        )
        info = DeploymentPolicyInfo(
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=rolling,
            blue_green=None,
        )
        json_str = info.model_dump_json()
        restored = DeploymentPolicyInfo.model_validate_json(json_str)
        assert restored.strategy == info.strategy
        assert restored.rolling_update is not None
        assert restored.rolling_update.max_surge.count == 2
        assert restored.blue_green is None
