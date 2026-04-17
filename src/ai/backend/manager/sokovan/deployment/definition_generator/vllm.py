from typing import override

from ai.backend.common.config import (
    ModelConfigDraft,
    ModelDefinitionDraft,
    ModelHealthCheckDraft,
    ModelServiceConfigDraft,
)
from ai.backend.common.types import MODEL_SERVICE_RUNTIME_PROFILES
from ai.backend.manager.sokovan.deployment.definition_generator.base import (
    ModelDefinitionContext,
    ModelDefinitionGenerator,
)


class VLLMModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for vLLM runtime variant."""

    @override
    async def generate_model_definition(
        self, context: ModelDefinitionContext
    ) -> ModelDefinitionDraft:
        runtime_profile = MODEL_SERVICE_RUNTIME_PROFILES["vllm"]

        health_check: ModelHealthCheckDraft | None = None
        if runtime_profile.health_check_endpoint:
            health_check = ModelHealthCheckDraft(
                path=runtime_profile.health_check_endpoint,
                interval=10.0,
                max_retries=10,
                initial_delay=1800.0,
            )

        model = ModelConfigDraft(
            name="vllm-model",
            model_path=context.mounts.model_mount_destination,
            service=ModelServiceConfigDraft(
                start_command=context.execution.startup_command or "",
                port=runtime_profile.port or 8000,
                health_check=health_check,
            ),
        )

        return ModelDefinitionDraft(models=[model])
