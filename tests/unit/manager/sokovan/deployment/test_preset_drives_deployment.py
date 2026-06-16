"""A preset that satisfies the required-field contract is enough on its
own to drive ``DeploymentController.create_deployment`` to a created
endpoint — the model_card.deploy invariant.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.creator import (
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentOptions,
)
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
)
from ai.backend.manager.repositories.deployment.creators.deployment import (
    DeploymentCreatorSpec,
)
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)


class TestDeploymentFromPreset:
    @pytest.fixture
    def preset_data(self) -> DeploymentRevisionPresetData:
        return DeploymentRevisionPresetData(
            id=DeploymentPresetID(uuid.uuid4()),
            runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            name="self-sufficient",
            description=None,
            rank=100,
            image_id=ImageID(uuid.uuid4()),
            model_definition=None,
            resource_opts=[],
            cluster_mode="single-node",
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ=[],
            runtime_variant_preset_values=[],
            replica_count=3,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
            open_to_public=True,
            revision_history_limit=20,
            created_at=datetime(2026, 4, 30, tzinfo=UTC),
            updated_at=None,
        )

    @pytest.fixture
    def mock_preset_repository(self, preset_data: DeploymentRevisionPresetData) -> MagicMock:
        repository = MagicMock(spec=DeploymentRevisionPresetRepository)
        repository.get_by_id = AsyncMock(return_value=preset_data)
        return repository

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.get_resource_group_default_deployment_options = AsyncMock(
            return_value=DeploymentOptions()
        )
        repository.create_endpoint = AsyncMock(return_value=MagicMock())
        return repository

    @pytest.fixture
    def deployment_controller(
        self,
        mock_preset_repository: MagicMock,
        mock_deployment_repository: MagicMock,
    ) -> DeploymentController:
        return DeploymentController(
            DeploymentControllerArgs(
                scheduling_controller=MagicMock(),
                deployment_repository=mock_deployment_repository,
                config_provider=MagicMock(),
                storage_manager=MagicMock(),
                event_producer=MagicMock(),
                valkey_schedule=MagicMock(),
                revision_draft_reader=MagicMock(),
                deployment_revision_preset_repository=mock_preset_repository,
            )
        )

    @pytest.fixture
    def preset_only_creator(
        self, preset_data: DeploymentRevisionPresetData
    ) -> NewDeploymentCreator:
        """A creator that references only the preset — every deployment-level
        field is left ``None`` so resolution must come entirely from the preset."""
        return NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name="preset-driven",
                domain="default",
                project=uuid.uuid4(),
                resource_group="default",
                created_user=uuid.uuid4(),
                session_owner=uuid.uuid4(),
                created_at=None,
                revision_history_limit=None,
            ),
            replica_spec=None,
            network=None,
            policy=None,
            model_revision=ModelRevisionCreator(
                image_id=None,
                mounts=VFolderMountsCreator(
                    model_vfolder_id=VFolderUUID(uuid.uuid4()),
                    model_definition_path=None,
                    model_mount_destination="/models",
                    extra_mounts=[],
                ),
                revision_preset_id=preset_data.id,
            ),
        )

    async def test_preset_alone_drives_endpoint_creation(
        self,
        deployment_controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        preset_only_creator: NewDeploymentCreator,
        preset_data: DeploymentRevisionPresetData,
    ) -> None:
        await deployment_controller.create_deployment(preset_only_creator)

        mock_deployment_repository.create_endpoint.assert_awaited_once()
        rbac_creator, policy_config = mock_deployment_repository.create_endpoint.await_args.args
        spec: DeploymentCreatorSpec = rbac_creator.spec
        assert spec.replica.replica_count == preset_data.replica_count
        assert spec.network.open_to_public == preset_data.open_to_public
        assert spec.metadata.revision_history_limit == preset_data.revision_history_limit
        assert policy_config is not None
        assert policy_config.strategy == preset_data.deployment_strategy
