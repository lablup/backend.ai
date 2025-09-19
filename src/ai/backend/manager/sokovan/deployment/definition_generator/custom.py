from typing import Any, override

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.data.deployment.types import (
    DefinitionFiles,
    ModelRevisionSpec,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator


class CustomModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for custom runtime variant."""

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    @override
    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        definition_files: DefinitionFiles = (
            await self._deployment_repository.fetch_definition_files(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                model_definition_path=model_revision.mounts.model_definition_path,
            )
        )
        return ModelDefinition.model_validate(definition_files.model_definition)

    @override
    async def validate_configuration(self, config: dict) -> None:
        # Already validated during generation
        pass

    async def _validate_model_definition_dict(self, model_definition: dict[str, Any]) -> None:
        ModelDefinition.model_validate(model_definition)

    @override
    async def generate_model_revision(self, model_revision: ModelRevisionSpec) -> ModelRevisionSpec:
        definition_files: DefinitionFiles = (
            await self._deployment_repository.fetch_definition_files(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                model_definition_path=model_revision.mounts.model_definition_path,
            )
        )
        await self._validate_model_definition_dict(definition_files.model_definition)
        if definition_files.service_definition is None:
            return model_revision
        service_definition = ModelServiceDefinition.model_validate(
            definition_files.service_definition
        )
        return service_definition.override_model_revision(model_revision)
