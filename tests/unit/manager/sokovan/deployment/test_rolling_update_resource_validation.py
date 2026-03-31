"""Tests for deployment surge resource validation in DeploymentController.

Tests verify that validate_deployment_surge_resources correctly checks
whether the scaling group has enough free resources to accommodate
the surge of a deployment (max_surge for rolling update, full replica
count for blue-green).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant, SlotQuantity
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
from ai.backend.manager.data.scaling_group.types import ResourceInfo
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    RollingUpdateSpec,
)
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)

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


def _make_resource_info(
    free_slots: dict[str, Decimal],
) -> ResourceInfo:
    """Create ResourceInfo with the given free slots."""
    capacity = {k: v * 10 for k, v in free_slots.items()}
    used = {k: capacity[k] - v for k, v in free_slots.items()}
    return ResourceInfo(
        capacity=[SlotQuantity(k, v) for k, v in capacity.items()],
        used=[SlotQuantity(k, v) for k, v in used.items()],
        free=[SlotQuantity(k, v) for k, v in free_slots.items()],
    )


class TestValidateDeploymentSurgeResources:
    """Tests for DeploymentController.validate_deployment_surge_resources."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_scaling_group_repository(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def controller(
        self,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> DeploymentController:
        args = MagicMock(spec=DeploymentControllerArgs)
        args.scheduling_controller = MagicMock()
        args.deployment_repository = mock_deployment_repository
        args.scaling_group_repository = mock_scaling_group_repository
        args.config_provider = MagicMock()
        args.storage_manager = MagicMock()
        args.event_producer = MagicMock()
        args.valkey_schedule = MagicMock()
        args.revision_generator_registry = MagicMock()
        return DeploymentController(args)

    async def test_blue_green_pass_when_resources_are_sufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Blue-green requires target_replica_count worth of surge resources."""
        deployment_info = _make_deployment_info()  # replica_count=2
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
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # Blue-green surge = 2 replicas * (2 cpu, 4096 mem) = (4 cpu, 8192 mem)
        # Free resources are (8 cpu, 16384 mem) — sufficient
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is True

    async def test_blue_green_fail_when_resources_are_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Blue-green returns insufficient when free < replica_count * per_route."""
        deployment_info = _make_deployment_info()  # replica_count=2
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
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # Blue-green surge = 2 replicas * (2 cpu, 4096 mem) = (4 cpu, 8192 mem)
        # Free resources are (1 cpu, 2048 mem) — insufficient
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is False
        assert result.strategy == DeploymentStrategy.BLUE_GREEN
        assert result.surge_count == 2
        assert result.insufficient_details is not None
        assert any("cpu" in d for d in result.insufficient_details)
        assert any("mem" in d for d in result.insufficient_details)

    async def test_skip_validation_when_max_surge_is_zero(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Rolling update with max_surge=0 needs no surge resources."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=0), max_unavailable=IntOrPercent(count=1)
                ),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is True

        mock_scaling_group_repository.get_resource_info.assert_not_called()

    async def test_pass_when_resources_are_sufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Validation passes when free resources >= surge requirements."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=2), max_unavailable=IntOrPercent(count=0)
                ),
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
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is True

    async def test_fail_when_resources_are_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Validation returns insufficient when free resources < surge."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=2), max_unavailable=IntOrPercent(count=0)
                ),
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
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is False
        assert result.strategy == DeploymentStrategy.ROLLING
        assert result.surge_count == 2
        assert result.scaling_group == "default"
        assert result.insufficient_details is not None
        assert any("cpu" in d for d in result.insufficient_details)
        assert any("mem" in d for d in result.insufficient_details)

    async def test_fail_when_single_resource_is_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Validation fails even if only one resource type is insufficient."""
        deployment_info = _make_deployment_info()
        mock_deployment_repository.get_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyData(
                id=uuid.uuid4(),
                endpoint=ENDPOINT_ID,
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
                ),
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
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("10"),
                "mem": Decimal("2048"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is False
        assert result.insufficient_details is not None
        assert any("mem" in d for d in result.insufficient_details)
        # CPU should NOT be in insufficient details since it's sufficient
        assert not any("cpu" in d for d in result.insufficient_details)

    async def test_correct_scaling_group_is_queried(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
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
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
                ),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("1")},
            )
        )
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({"cpu": Decimal("100")})
        )

        await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)

        mock_scaling_group_repository.get_resource_info.assert_called_once_with("my-gpu-group")
