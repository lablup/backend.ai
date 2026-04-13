"""Unit tests for DeploymentService._apply_deployment_level_preset.

Verifies that deployment-level fields on a NewDeploymentCreator are correctly
resolved against the revision preset defaults using the priority:
explicit caller input > preset default > system default.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
)
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)


def _make_preset(
    *,
    open_to_public: bool | None = None,
    replica_count: int | None = None,
    revision_history_limit: int | None = None,
    deployment_strategy: DeploymentStrategy | None = None,
    deployment_strategy_spec: dict[str, Any] | None = None,
) -> DeploymentRevisionPresetData:
    """Build a minimal preset data object with the given deployment-level overrides."""
    return DeploymentRevisionPresetData(
        id=uuid.uuid4(),
        runtime_variant_id=uuid.uuid4(),
        name="test-preset",
        description=None,
        rank=100,
        image_id=uuid.uuid4(),
        model_definition=None,
        resource_opts=[],
        cluster_mode="single-node",
        cluster_size=1,
        startup_command=None,
        bootstrap_script=None,
        environ=[],
        preset_values=[],
        open_to_public=open_to_public,
        replica_count=replica_count,
        revision_history_limit=revision_history_limit,
        deployment_strategy=deployment_strategy,
        deployment_strategy_spec=deployment_strategy_spec,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=None,
    )


def _make_creator(
    preset_id: uuid.UUID | None,
    *,
    metadata_history_limit: int | None = None,
    replica_spec: ReplicaSpec | None = None,
    network: DeploymentNetworkSpec | None = None,
    policy: DeploymentPolicyConfig | None = None,
) -> NewDeploymentCreator:
    """Build a minimal NewDeploymentCreator referencing the given preset id."""
    return NewDeploymentCreator(
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid.uuid4(),
            resource_group="default",
            created_user=uuid.uuid4(),
            session_owner=uuid.uuid4(),
            created_at=None,
            revision_history_limit=metadata_history_limit,
        ),
        replica_spec=replica_spec,
        network=network,
        model_revision=ModelRevisionCreator(
            image_id=None,
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={},
            ),
            mounts=VFolderMountsCreator(model_vfolder_id=uuid.uuid4()),
            execution=ExecutionSpec(runtime_variant=RuntimeVariant("custom")),
            model_definition=None,
            revision_preset_id=preset_id,
        ),
        policy=policy,
    )


@pytest.fixture
def mock_preset_repository() -> MagicMock:
    return MagicMock(spec=DeploymentRevisionPresetRepository)


@pytest.fixture
def deployment_service(mock_preset_repository: MagicMock) -> DeploymentService:
    return DeploymentService(
        deployment_controller=MagicMock(spec=DeploymentController),
        deployment_repository=MagicMock(spec=DeploymentRepository),
        revision_generator_registry=MagicMock(spec=RevisionGeneratorRegistry),
        model_definition_generator_registry=AsyncMock(),
        deployment_revision_preset_repository=mock_preset_repository,
    )


class TestApplyDeploymentLevelPreset:
    async def test_no_preset_id_falls_back_to_system_defaults(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """When the creator does not reference any preset, system defaults are used."""
        creator = _make_creator(preset_id=None)
        resolved = await deployment_service._apply_deployment_level_preset(creator)

        assert resolved.metadata.revision_history_limit == 10
        assert resolved.replica_spec is not None
        assert resolved.replica_spec.replica_count == 1
        assert resolved.network is not None
        assert resolved.network.open_to_public is False
        assert resolved.policy is None
        mock_preset_repository.get_by_id.assert_not_called()

    async def test_preset_provides_all_defaults(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """All five preset fields are applied when the caller leaves them unset."""
        preset_id = uuid.uuid4()
        mock_preset_repository.get_by_id = AsyncMock(
            return_value=_make_preset(
                open_to_public=True,
                replica_count=3,
                revision_history_limit=20,
                deployment_strategy=DeploymentStrategy.BLUE_GREEN,
                deployment_strategy_spec={"auto_promote": True, "promote_delay_seconds": 5},
            )
        )
        creator = _make_creator(preset_id=preset_id)

        resolved = await deployment_service._apply_deployment_level_preset(creator)

        assert resolved.metadata.revision_history_limit == 20
        assert resolved.replica_spec is not None
        assert resolved.replica_spec.replica_count == 3
        assert resolved.network is not None
        assert resolved.network.open_to_public is True
        assert resolved.policy is not None
        assert resolved.policy.strategy == DeploymentStrategy.BLUE_GREEN
        assert isinstance(resolved.policy.strategy_spec, BlueGreenSpec)
        assert resolved.policy.strategy_spec.auto_promote is True
        assert resolved.policy.strategy_spec.promote_delay_seconds == 5
        mock_preset_repository.get_by_id.assert_awaited_once_with(preset_id)

    async def test_caller_input_wins_over_preset(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """When the caller specifies a value, the preset default is ignored."""
        preset_id = uuid.uuid4()
        mock_preset_repository.get_by_id = AsyncMock(
            return_value=_make_preset(
                open_to_public=True,
                replica_count=5,
                revision_history_limit=99,
                deployment_strategy=DeploymentStrategy.ROLLING,
            )
        )
        explicit_policy = DeploymentPolicyConfig(
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=False, promote_delay_seconds=0),
        )
        creator = _make_creator(
            preset_id=preset_id,
            metadata_history_limit=7,
            replica_spec=ReplicaSpec(replica_count=2),
            network=DeploymentNetworkSpec(open_to_public=False),
            policy=explicit_policy,
        )

        resolved = await deployment_service._apply_deployment_level_preset(creator)

        assert resolved.metadata.revision_history_limit == 7
        assert resolved.replica_spec is not None
        assert resolved.replica_spec.replica_count == 2
        assert resolved.network is not None
        assert resolved.network.open_to_public is False
        assert resolved.policy is explicit_policy

    async def test_partial_preset_falls_back_per_field(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """Each preset field falls back to system default independently when null."""
        preset_id = uuid.uuid4()
        mock_preset_repository.get_by_id = AsyncMock(
            return_value=_make_preset(
                open_to_public=True,
                # replica_count, revision_history_limit, deployment_strategy left as None
            )
        )
        creator = _make_creator(preset_id=preset_id)

        resolved = await deployment_service._apply_deployment_level_preset(creator)

        # Specified by preset.
        assert resolved.network is not None
        assert resolved.network.open_to_public is True
        # Falls back to system defaults.
        assert resolved.metadata.revision_history_limit == 10
        assert resolved.replica_spec is not None
        assert resolved.replica_spec.replica_count == 1
        assert resolved.policy is None

    async def test_preset_rolling_strategy_with_int_or_percent_spec(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """Rolling-update strategy_spec is reconstructed from JSON dict."""
        preset_id = uuid.uuid4()
        rolling_dict = RollingUpdateSpec(
            max_surge=IntOrPercent(count=3),
            max_unavailable=IntOrPercent(percent=0.25),
        ).model_dump(mode="json")
        mock_preset_repository.get_by_id = AsyncMock(
            return_value=_make_preset(
                deployment_strategy=DeploymentStrategy.ROLLING,
                deployment_strategy_spec=rolling_dict,
            )
        )
        creator = _make_creator(preset_id=preset_id)

        resolved = await deployment_service._apply_deployment_level_preset(creator)

        assert resolved.policy is not None
        assert resolved.policy.strategy == DeploymentStrategy.ROLLING
        assert isinstance(resolved.policy.strategy_spec, RollingUpdateSpec)
        assert resolved.policy.strategy_spec.max_surge.count == 3
        assert resolved.policy.strategy_spec.max_unavailable.percent == 0.25

    async def test_preset_strategy_without_spec_uses_default_spec(
        self,
        deployment_service: DeploymentService,
        mock_preset_repository: MagicMock,
    ) -> None:
        """When the preset stores strategy without spec, the default spec is built."""
        preset_id = uuid.uuid4()
        mock_preset_repository.get_by_id = AsyncMock(
            return_value=_make_preset(
                deployment_strategy=DeploymentStrategy.ROLLING,
                deployment_strategy_spec=None,
            )
        )
        creator = _make_creator(preset_id=preset_id)

        resolved = await deployment_service._apply_deployment_level_preset(creator)

        assert resolved.policy is not None
        assert isinstance(resolved.policy.strategy_spec, RollingUpdateSpec)
