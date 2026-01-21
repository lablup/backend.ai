"""Registry for managing revision processors by runtime variant."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.exception import RuntimeVariantNotSupportedError
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.abc import (
    RevisionGenerator,
)
from ai.backend.manager.sokovan.deployment.revision_generator.base import (
    BaseRevisionGenerator,
)
from ai.backend.manager.sokovan.deployment.revision_generator.custom import (
    CustomRevisionGenerator,
)


@dataclass
class RevisionGeneratorRegistryArgs:
    deployment_repository: DeploymentRepository


class RevisionGeneratorRegistry:
    """
    Registry for managing revision processors by runtime variant.

    Most variants share the same base implementation (BaseRevisionProcessor),
    while CUSTOM has additional validation logic (CustomRevisionProcessor).
    """

    _generators: dict[RuntimeVariant, RevisionGenerator]

    def __init__(self, args: RevisionGeneratorRegistryArgs) -> None:
        repo = args.deployment_repository

        # CUSTOM variant has special validation for model definition
        custom_generator = CustomRevisionGenerator(repo)

        # All other variants use the base generator
        base_generator = BaseRevisionGenerator(repo)

        self._generators: dict[RuntimeVariant, RevisionGenerator] = {
            RuntimeVariant.CUSTOM: custom_generator,
            RuntimeVariant.VLLM: base_generator,
            RuntimeVariant.HUGGINGFACE_TGI: base_generator,
            RuntimeVariant.NIM: base_generator,
            RuntimeVariant.SGLANG: base_generator,
            RuntimeVariant.MODULAR_MAX: base_generator,
            RuntimeVariant.CMD: base_generator,
        }

    def get(self, runtime_variant: RuntimeVariant) -> RevisionGenerator:
        generator = self._generators.get(runtime_variant)
        if generator is None:
            raise RuntimeVariantNotSupportedError(runtime_variant)
        return generator
