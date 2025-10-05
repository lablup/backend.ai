from typing import override

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
)
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator


class CMDModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for CMD runtime variant."""

    @override
    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        # CMD variant uses a fixed port of 8000 and no health check by default
        model = ModelConfig(
            name="image-model",
            model_path=model_revision.mounts.model_mount_destination,
            service=ModelServiceConfig(
                start_command=model_revision.execution.startup_command or "",
                port=8000,  # Default port for CMD variant
                health_check=None,  # No health check for CMD variant
            ),
        )

        return ModelDefinition(models=[model])

    @override
    async def generate_model_revision(self, model_revision: ModelRevisionSpec) -> ModelRevisionSpec:
        # For non-custom variants, we don't modify the model revision
        return model_revision
