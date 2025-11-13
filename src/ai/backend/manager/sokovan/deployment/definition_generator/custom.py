from typing import override

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.data.deployment.types import (
    DefinitionFiles,
    ModelRevisionSpec,
    ModelServiceDefinition,
    RequestedModelRevisionSpec,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator


class CustomModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for custom runtime variant."""

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    @override
    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        definition_files = await self._deployment_repository.fetch_definition_files(
            vfolder_id=model_revision.mounts.model_vfolder_id,
            model_definition_path=model_revision.mounts.model_definition_path,
        )
        return ModelDefinition.model_validate(definition_files.model_definition)

    @override
    async def generate_model_revision(
        self, requested_model_revision: RequestedModelRevisionSpec
    ) -> ModelRevisionSpec:
        definition_files: DefinitionFiles = (
            await self._deployment_repository.fetch_definition_files(
                vfolder_id=requested_model_revision.mounts.model_vfolder_id,
                model_definition_path=requested_model_revision.mounts.model_definition_path,
            )
        )
        ModelDefinition.model_validate(definition_files.model_definition)
        if definition_files.service_definition is None:
            return requested_model_revision.to_model_revision_spec()
        service_definition = ModelServiceDefinition.model_validate(
            definition_files.service_definition
        )
        return requested_model_revision.to_model_revision_spec_with_service_definition(
            service_definition=service_definition
        )
