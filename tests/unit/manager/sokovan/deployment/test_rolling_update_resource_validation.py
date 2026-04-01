"""Tests for deployment surge resource validation in DeploymentController.

Tests verify that check_deployment_surge_resources correctly checks
whether the scaling group has enough free resources to accommodate
the surge of a deployment (max_surge for rolling update, full replica
count for blue-green).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
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


@dataclass(frozen=True)
class SurgeResourceCase:
    """A single parametrized case for surge resource validation."""

    strategy: DeploymentStrategy
    strategy_spec: BlueGreenSpec | RollingUpdateSpec
    resource_slots: dict[str, Decimal]
    free_slots: dict[str, Decimal]
    expected_sufficient: bool
    expected_surge_count: int
    cluster_size: int = 1


def _make_deployment_info(
    *,
    policy: DeploymentPolicyData,
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
        policy=policy,
    )


def _make_revision_data(
    *,
    resource_slots: dict[str, Decimal],
    cluster_size: int = 1,
) -> ModelRevisionData:
    """Create a ModelRevisionData with the given resource slots."""
    return ModelRevisionData(
        id=REVISION_ID,
        name="v1",
        cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=cluster_size),
        resource_config=ResourceConfigData(
            resource_group_name="default",
            resource_slot=ResourceSlot(resource_slots),
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


class TestCheckDeploymentSurgeResources:
    """Tests for DeploymentController.check_deployment_surge_resources."""

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

    @pytest.mark.parametrize(
        "case",
        [
            SurgeResourceCase(
                strategy=DeploymentStrategy.BLUE_GREEN,
                strategy_spec=BlueGreenSpec(auto_promote=False),
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                free_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                expected_sufficient=True,
                expected_surge_count=2,
            ),
            SurgeResourceCase(
                strategy=DeploymentStrategy.BLUE_GREEN,
                strategy_spec=BlueGreenSpec(auto_promote=False),
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                free_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
                expected_sufficient=False,
                expected_surge_count=2,
            ),
            SurgeResourceCase(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=2), max_unavailable=IntOrPercent(count=0)
                ),
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                free_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                expected_sufficient=True,
                expected_surge_count=2,
            ),
            SurgeResourceCase(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=2), max_unavailable=IntOrPercent(count=0)
                ),
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                free_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
                expected_sufficient=False,
                expected_surge_count=2,
            ),
        ],
        ids=[
            "blue_green-sufficient",
            "blue_green-insufficient",
            "rolling-sufficient",
            "rolling-insufficient",
        ],
    )
    async def test_surge_resource_check(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
        case: SurgeResourceCase,
    ) -> None:
        """Surge resource check for both blue-green and rolling strategies."""
        policy = DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=ENDPOINT_ID,
            strategy=case.strategy,
            strategy_spec=case.strategy_spec,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deployment_info = _make_deployment_info(policy=policy)
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(resource_slots=case.resource_slots)
        )
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info(case.free_slots)
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is case.expected_sufficient
        if not case.expected_sufficient:
            assert result.shortfall is not None
            assert result.shortfall.strategy == case.strategy
            assert result.shortfall.surge_count == case.expected_surge_count

    async def test_skip_validation_when_max_surge_is_zero(
        self,
        controller: DeploymentController,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Rolling update with max_surge=0 needs no surge resources."""
        policy = DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=ENDPOINT_ID,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=0), max_unavailable=IntOrPercent(count=1)
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deployment_info = _make_deployment_info(policy=policy)

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is True
        mock_scaling_group_repository.get_resource_info.assert_not_called()

    async def test_fail_when_single_resource_is_insufficient(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Validation fails even if only one resource type is insufficient."""
        policy = DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=ENDPOINT_ID,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deployment_info = _make_deployment_info(policy=policy)
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            )
        )
        # CPU is sufficient (10) but mem is insufficient (2048)
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({
                "cpu": Decimal("10"),
                "mem": Decimal("2048"),
            })
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is False
        assert result.shortfall is not None
        assert any("mem" in d for d in result.shortfall.insufficient_slots)
        assert not any("cpu" in d for d in result.shortfall.insufficient_slots)

    async def test_correct_scaling_group_is_queried(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
    ) -> None:
        """Validation queries the correct scaling group from deployment metadata."""
        policy = DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=ENDPOINT_ID,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deployment_info = _make_deployment_info(policy=policy, resource_group="my-gpu-group")
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(resource_slots={"cpu": Decimal("1")}),
        )
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info({"cpu": Decimal("100")})
        )

        await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        mock_scaling_group_repository.get_resource_info.assert_called_once_with("my-gpu-group")

    @pytest.mark.parametrize(
        "case",
        [
            SurgeResourceCase(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
                ),
                resource_slots={"cpu": Decimal("4")},
                free_slots={"cpu": Decimal("6")},
                expected_sufficient=False,
                cluster_size=2,
            ),
            SurgeResourceCase(
                strategy=DeploymentStrategy.ROLLING,
                strategy_spec=RollingUpdateSpec(
                    max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
                ),
                resource_slots={"cpu": Decimal("4")},
                free_slots={"cpu": Decimal("10")},
                expected_sufficient=True,
                cluster_size=2,
            ),
        ],
        ids=["insufficient", "sufficient"],
    )
    async def test_cluster_size_multiplies_surge_resource_requirement(
        self,
        controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        mock_scaling_group_repository: MagicMock,
        case: SurgeResourceCase,
    ) -> None:
        """Surge resources must account for cluster_size > 1.

        surge_count=1 (max_surge) * cluster_size=2 = 2 total kernels
        per_route_slots: cpu=4 → total surge = 4 * 2 = 8 cpu
        """
        policy = DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=ENDPOINT_ID,
            strategy=case.strategy,
            strategy_spec=case.strategy_spec,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deployment_info = _make_deployment_info(policy=policy)
        mock_deployment_repository.get_revision = AsyncMock(
            return_value=_make_revision_data(
                resource_slots=case.resource_slots,
                cluster_size=case.cluster_size,
            )
        )
        mock_scaling_group_repository.get_resource_info = AsyncMock(
            return_value=_make_resource_info(case.free_slots)
        )

        result = await controller.check_deployment_surge_resources(deployment_info, REVISION_ID)
        assert result.sufficient is case.expected_sufficient
