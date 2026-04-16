from typing import override

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import (
    ModelDefinitionContext,
    ModelDefinitionGenerator,
)


class CustomModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for custom runtime variant.

    Fetches the definition from the vfolder storage file. The file may be
    partial — required-field validation is deferred to the persistence
    boundary via ``ModelDefinitionDraft.to_resolved``.
    """

    _deployment_repository: DeploymentRepository

    def __init__(self, deployment_repository: DeploymentRepository) -> None:
        self._deployment_repository = deployment_repository

    @override
    async def generate_model_definition(
        self, context: ModelDefinitionContext
    ) -> ModelDefinitionDraft:
        model_definition_content = await self._deployment_repository.fetch_model_definition(
            vfolder_id=context.mounts.model_vfolder_id,
            model_definition_path=context.mounts.model_definition_path,
        )
        return ModelDefinitionDraft.model_validate(model_definition_content)
