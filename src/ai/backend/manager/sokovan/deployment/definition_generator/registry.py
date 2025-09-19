from dataclasses import dataclass

from ai.backend.common.exception import RuntimeVariantNotSupportedError
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionGenerator
from ai.backend.manager.sokovan.deployment.definition_generator.custom import (
    CustomModelDefinitionGenerator,
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

    def get(self, runtime_variant: RuntimeVariant) -> ModelDefinitionGenerator:
        generator = self._generators.get(runtime_variant)
        if generator is None:
            raise RuntimeVariantNotSupportedError(runtime_variant)
        return generator
