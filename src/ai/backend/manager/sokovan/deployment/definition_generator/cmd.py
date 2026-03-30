from typing import override

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
)
from ai.backend.manager.sokovan.deployment.definition_generator.base import (
    ModelDefinitionContext,
    ModelDefinitionGenerator,
)


class CMDModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for CMD runtime variant."""

    @override
    async def generate_model_definition(self, context: ModelDefinitionContext) -> ModelDefinition:
        # CMD variant uses a fixed port of 8000 and no health check by default
        model = ModelConfig(
            name="image-model",
            model_path=context.mounts.model_mount_destination,
            service=ModelServiceConfig(
                start_command=context.execution.startup_command or "",
                port=8000,  # Default port for CMD variant
                health_check=None,  # No health check for CMD variant
            ),
        )

        return ModelDefinition(models=[model])
