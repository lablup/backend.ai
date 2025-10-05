from typing import Optional, override

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelHealthCheck,
    ModelServiceConfig,
)
from ai.backend.common.types import MODEL_SERVICE_RUNTIME_PROFILES, RuntimeVariant
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator


class HuggingFaceTGIModelDefinitionGenerator(ModelDefinitionGenerator):
    """Model definition generator implementation for Hugging Face TGI runtime variant."""

    @override
    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        runtime_profile = MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.HUGGINGFACE_TGI]

        health_check: Optional[ModelHealthCheck] = None
        if runtime_profile.health_check_endpoint:
            health_check = ModelHealthCheck(
                path=runtime_profile.health_check_endpoint,
            )

        model = ModelConfig(
            name="tgi-model",
            model_path=model_revision.mounts.model_mount_destination,
            service=ModelServiceConfig(
                start_command=model_revision.execution.startup_command or "",
                port=runtime_profile.port or 3000,
                health_check=health_check,
            ),
        )

        return ModelDefinition(models=[model])

    @override
    async def generate_model_revision(self, model_revision: ModelRevisionSpec) -> ModelRevisionSpec:
        # For non-custom variants, we don't modify the model revision
        return model_revision
