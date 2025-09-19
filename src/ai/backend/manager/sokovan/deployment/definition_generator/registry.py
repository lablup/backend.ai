from dataclasses import dataclass

from ai.backend.common.exception import RuntimeVariantNotSupportedError
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator
from ai.backend.manager.sokovan.deployment.definition_generator.cmd import (
    CMDModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.custom import (
    CustomModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.huggingface_tgi import (
    HuggingFaceTGIModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.nim import (
    NIMModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.vllm import (
    VLLMModelDefinitionGenerator,
)


@dataclass
class RegistryArgs:
    deployment_repository: DeploymentRepository


class ModelDefinitionGeneratorRegistry:
    _generators: dict[RuntimeVariant, ModelDefinitionGenerator]

    def __init__(self, args: RegistryArgs) -> None:
        self._generators: dict[RuntimeVariant, ModelDefinitionGenerator] = {}
        self._generators[RuntimeVariant.CUSTOM] = CustomModelDefinitionGenerator(
            args.deployment_repository
        )
        self._generators[RuntimeVariant.VLLM] = VLLMModelDefinitionGenerator()
        self._generators[RuntimeVariant.HUGGINGFACE_TGI] = HuggingFaceTGIModelDefinitionGenerator()
        self._generators[RuntimeVariant.NIM] = NIMModelDefinitionGenerator()
        self._generators[RuntimeVariant.CMD] = CMDModelDefinitionGenerator()

    def get(self, runtime_variant: RuntimeVariant) -> ModelDefinitionGenerator:
        generator = self._generators.get(runtime_variant)
        if generator is None:
            raise RuntimeVariantNotSupportedError(runtime_variant)
        return generator
