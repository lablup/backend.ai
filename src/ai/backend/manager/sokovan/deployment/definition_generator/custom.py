from typing import Optional, override

from ai.backend.common.config import ModelDefinition
from ai.backend.common.exception import ServiceDefinitionNotLoadedError
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
    _service_definition: Optional[ModelServiceDefinition]

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository
        self._service_definition: Optional[ModelServiceDefinition] = None

    @override
    async def generate_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        definition_files: DefinitionFiles = (
            await self._deployment_repository.fetch_definition_files(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                model_definition_path=model_revision.mounts.model_definition_path,
            )
        )
        if definition_files.service_definition:
            self._service_definition = ModelServiceDefinition.model_validate(
                definition_files.service_definition
            )
        return ModelDefinition.model_validate(definition_files.model_definition)

    @override
    async def validate_configuration(self, config: dict) -> None:
        # Already validated during generation
        pass

    @override
    async def override_service_definition(
        self, model_revision: ModelRevisionSpec
    ) -> ModelRevisionSpec:
        if not self._service_definition:
            raise ServiceDefinitionNotLoadedError()
        model_revision = self._service_definition.override_model_revision(model_revision)
        self._service_definition = None
        return model_revision
