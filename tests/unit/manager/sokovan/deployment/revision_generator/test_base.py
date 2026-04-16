"""Tests for BaseRevisionGenerator and CustomRevisionGenerator validators.

The merge pipeline (deployment-config.yaml / preset / model-definition.yaml
/ request) now lives entirely in ``DeploymentController``; these generators
are reduced to variant-specific validators. Only CUSTOM has behaviour beyond
the no-op default.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.base import BaseRevisionGenerator
from ai.backend.manager.sokovan.deployment.revision_generator.custom import CustomRevisionGenerator


class TestDefinitionFileRequirement:
    """CUSTOM variant must validate model-definition.yaml; others are no-op."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def base_generator(self, mock_deployment_repository: MagicMock) -> BaseRevisionGenerator:
        return BaseRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def custom_generator(self, mock_deployment_repository: MagicMock) -> CustomRevisionGenerator:
        return CustomRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def vfolder_id(self) -> UUID:
        return uuid4()

    def _revision(
        self,
        runtime_variant: RuntimeVariant,
        vfolder_id: UUID,
    ) -> ModelRevisionSpec:
        return ModelRevisionSpec(
            image_id=uuid4(),
            image_identifier=ImageIdentifier(
                canonical="image:latest",
                architecture="x86_64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": 4, "mem": "8gb"},
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=vfolder_id,
                model_mount_destination="/models",
                model_definition_path=None,
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                runtime_variant=runtime_variant,
                startup_command="python app.py",
                bootstrap_script=None,
                environ=None,
            ),
        )

    @pytest.mark.parametrize(
        "runtime_variant",
        [
            RuntimeVariant("vllm"),
            RuntimeVariant("nim"),
            RuntimeVariant("huggingface-tgi"),
            RuntimeVariant("sglang"),
            RuntimeVariant("modular-max"),
            RuntimeVariant("cmd"),
        ],
        ids=lambda v: v,
    )
    async def test_base_validator_is_noop_for_non_custom_variants(
        self,
        runtime_variant: RuntimeVariant,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        revision = self._revision(runtime_variant, vfolder_id)
        await base_generator.validate_revision(revision)
        mock_deployment_repository.fetch_model_definition.assert_not_called()

    async def test_custom_variant_accepts_valid_model_definition(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            return_value={"models": [{"name": "test-model", "model-path": "/models/test-model"}]}
        )
        revision = self._revision(RuntimeVariant("custom"), vfolder_id)
        await custom_generator.validate_revision(revision)
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

    async def test_custom_variant_fails_when_definition_file_missing(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            side_effect=DefinitionFileNotFound
        )
        revision = self._revision(RuntimeVariant("custom"), vfolder_id)
        with pytest.raises(DefinitionFileNotFound):
            await custom_generator.validate_revision(revision)
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

    async def test_custom_variant_rejects_invalid_model_definition_schema(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            return_value={"models": "should_be_a_list_not_a_string"}
        )
        revision = self._revision(RuntimeVariant("custom"), vfolder_id)
        with pytest.raises(InvalidAPIParameters) as exc_info:
            await custom_generator.validate_revision(revision)
        assert "Invalid model definition for CUSTOM variant" in str(exc_info.value)
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )
