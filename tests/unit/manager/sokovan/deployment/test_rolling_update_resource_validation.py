"""Tests for rolling update resource validation in DeploymentController.

Tests verify that validate_rolling_update_resources correctly checks
whether the scaling group has enough free resources to accommodate
the max_surge of a rolling update deployment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicyData,
    DeploymentState,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ReplicaSpec,
    ResourceConfigData,
)
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    RollingUpdateSpec,
)
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.exceptions import InsufficientSurgeResources

ENDPOINT_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa")
REVISION_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
USER_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def _make_deployment_info(
    *,
    resource_group: str = "default",
) -> DeploymentInfo:
    """Create a DeploymentInfo for testing (revisions are fetched from repository)."""
    return DeploymentInfo(
        id=ENDPOINT_ID,
        metadata=DeploymentMetadata(
            name="test-deploy",
            domain="default",
            project=PROJECT_ID,
            resource_group=resource_group,
            created_user=USER_ID,
            session_owner=USER_ID,
            created_at=datetime.now(UTC),
            revision_history_limit=5,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.READY,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(replica_count=2),
        network=DeploymentNetworkSpec(open_to_public=False),
        model_revisions=[],
        current_revision_id=REVISION_ID,
    )


def _make_revision_data(
    *,
    resource_slots: dict[str, Decimal] | None = None,
) -> ModelRevisionData:
    """Create a ModelRevisionData with the given resource slots."""
    slots = resource_slots or {"cpu": Decimal("2"), "mem": Decimal("4096")}
    return ModelRevisionData(
        id=REVISION_ID,
        name="v1",
        cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=1),
        resource_config=ResourceConfigData(
            resource_group_name="default",
            resource_slot=ResourceSlot(slots),
        ),
        model_runtime_config=ModelRuntimeConfigData(runtime_variant=RuntimeVariant.CUSTOM),
        model_mount_config=ModelMountConfigData(
            vfolder_id=None,
            mount_destination="/models",
            definition_path="model-definition.yaml",
        ),
        created_at=datetime.now(UTC),
        image_id=uuid.uuid4(),
    )


def _make_total_resource_data(
    free_slots: dict[str, Decimal],
) -> TotalResourceData:
    """Create TotalResourceData with the given free slots."""
    capacity = {k: v * 10 for k, v in free_slots.items()}
    used = {k: capacity[k] - v for k, v in free_slots.items()}
    return TotalResourceData(
        total_used_slots=ResourceSlot(used),
        total_free_slots=ResourceSlot(free_slots),
        total_capacity_slots=ResourceSlot(capacity),
    )


class TestValidateRollingUpdateResources:
    """Tests for DeploymentController.validate_rolling_update_resources."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def controller(
        self,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> DeploymentController:
        args = MagicMock(spec=DeploymentControllerArgs)
        args.scheduling_controller = mock_scheduling_controller
        args.deployment_repository = mock_deployment_repository
        args.config_provider = MagicMock()
        args.storage_manager = MagicMock()
        args.event_producer = MagicMock()
        args.valkey_schedule = MagicMock()
        args.revision_generator_registry = MagicMock()
        return DeploymentController(args)

    async def test_skip_validation_for_blue_green_strategy(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Blue-green deployments should not be validated for surge resources."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.BLUE_GREEN,
                strategy_spec=BlueGreenSpec(auto_promote=False),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        # Should not raise
        await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

        # Should not check resources
        mock_scheduling_controller.get_available_resources_for_scaling_group.assert_not_called()

    async def test_skip_validation_when_max_surge_is_zero(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Rolling update with max_surge=0 needs no surge resources."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(max_surge=0, max_unavailable=1),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

        mock_scheduling_controller.get_available_resources_for_scaling_group.assert_not_called()

    async def test_pass_when_resources_are_sufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Validation passes when free resources >= surge requirements."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(max_surge=2, max_unavailable=0),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # Surge requires 2 * (2 cpu, 4096 mem) = (4 cpu, 8192 mem)
        # Free resources are (8 cpu, 16384 mem) — sufficient
        mock_scheduling_controller.get_available_resources_for_scaling_group = AsyncMock(
            return_value=_make_total_resource_data({
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            })
        )

        # Should not raise
        await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

    async def test_fail_when_resources_are_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Validation raises InsufficientSurgeResources when free resources < surge."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(max_surge=2, max_unavailable=0),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # Surge requires 2 * (2 cpu, 4096 mem) = (4 cpu, 8192 mem)
        # Free resources are (1 cpu, 2048 mem) — insufficient
        mock_scheduling_controller.get_available_resources_for_scaling_group = AsyncMock(
            return_value=_make_total_resource_data({
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
            })
        )

        with pytest.raises(InsufficientSurgeResources) as exc_info:
            await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

        error_message = str(exc_info.value)
        assert "max_surge=2" in error_message
        assert "cpu" in error_message
        assert "mem" in error_message
        assert "default" in error_message  # scaling group name

    async def test_fail_when_single_resource_is_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Validation fails even if only one resource type is insufficient."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # Surge requires 1 * (2 cpu, 4096 mem) = (2 cpu, 4096 mem)
        # CPU is sufficient (10) but mem is insufficient (2048)
        mock_scheduling_controller.get_available_resources_for_scaling_group = AsyncMock(
            return_value=_make_total_resource_data({
                "cpu": Decimal("10"),
                "mem": Decimal("2048"),
            })
        )

        with pytest.raises(InsufficientSurgeResources) as exc_info:
            await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

        error_message = str(exc_info.value)
        assert "mem" in error_message
        # CPU should NOT be in insufficient details since it's sufficient
        assert "cpu: required" not in error_message

    async def test_correct_scaling_group_is_queried(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scheduling_controller: MagicMock,
    ) -> None:
        """Validation queries the correct scaling group from deployment metadata."""
        deployment_info = _make_deployment_info(
            resource_group="my-gpu-group",
        )
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("1")},
            )
        )
        mock_scheduling_controller.get_available_resources_for_scaling_group = AsyncMock(
            return_value=_make_total_resource_data({"cpu": Decimal("100")})
        )

        await controller.validate_rolling_update_resources(deployment_info, REVISION_ID)

        mock_scheduling_controller.get_available_resources_for_scaling_group.assert_called_once_with(
            "my-gpu-group"
        )
