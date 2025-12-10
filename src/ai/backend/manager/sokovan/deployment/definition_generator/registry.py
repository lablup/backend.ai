from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.config import ModelDefinition
from ai.backend.common.exception import RuntimeVariantNotSupportedError
from ai.backend.common.types import RuntimeVariant
from ai.backend.common.utils import deep_merge
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
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
from ai.backend.manager.sokovan.deployment.definition_generator.modular_max import (
    ModularMAXModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.nim import (
    NIMModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.sglang import (
    SGLangModelDefinitionGenerator,
)
from ai.backend.manager.sokovan.deployment.definition_generator.vllm import (
    VLLMModelDefinitionGenerator,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import ModelRevisionSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class RegistryArgs:
    deployment_repository: DeploymentRepository
    enable_model_definition_override: bool = False


class ModelDefinitionGeneratorRegistry:
    _generators: dict[RuntimeVariant, ModelDefinitionGenerator]
    _deployment_repository: DeploymentRepository
    _enable_model_definition_override: bool

    def __init__(self, args: RegistryArgs) -> None:
        self._deployment_repository = args.deployment_repository
        self._enable_model_definition_override = args.enable_model_definition_override
        self._generators: dict[RuntimeVariant, ModelDefinitionGenerator] = {}
        self._generators[RuntimeVariant.CUSTOM] = CustomModelDefinitionGenerator(
            args.deployment_repository
        )
        self._generators[RuntimeVariant.VLLM] = VLLMModelDefinitionGenerator()
        self._generators[RuntimeVariant.HUGGINGFACE_TGI] = HuggingFaceTGIModelDefinitionGenerator()
        self._generators[RuntimeVariant.NIM] = NIMModelDefinitionGenerator()
        self._generators[RuntimeVariant.SGLANG] = SGLangModelDefinitionGenerator()
        self._generators[RuntimeVariant.MODULAR_MAX] = ModularMAXModelDefinitionGenerator()
        self._generators[RuntimeVariant.CMD] = CMDModelDefinitionGenerator()

    def get(self, runtime_variant: RuntimeVariant) -> ModelDefinitionGenerator:
        generator = self._generators.get(runtime_variant)
        if generator is None:
            raise RuntimeVariantNotSupportedError(runtime_variant)
        return generator

    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        """
        Generate a model definition for the given model revision.

        For CUSTOM variant: Always fetches from storage.
        For other variants:
            - Generate programmatically first
            - If enable_model_definition_override is True and model_definition_path exists,
              try to fetch from storage and deep merge (override) with generated definition
            - If fetch fails, use generated definition as fallback
        """
        runtime_variant = model_revision.execution.runtime_variant
        generator = self.get(runtime_variant)

        # For CUSTOM variant, always use the generator (which fetches from storage)
        if runtime_variant == RuntimeVariant.CUSTOM:
            return await generator.generate_model_definition(model_revision)

        # For other variants, generate first
        generated_definition = await generator.generate_model_definition(model_revision)

        # Check if override is enabled and path exists
        if not self._enable_model_definition_override:
            return generated_definition

        model_definition_path = model_revision.mounts.model_definition_path
        if not model_definition_path:
            return generated_definition

        # Try to fetch override from storage and merge
        return await self._try_apply_override(
            model_revision=model_revision,
            base_definition=generated_definition,
        )

    async def _try_apply_override(
        self,
        model_revision: ModelRevisionSpec,
        base_definition: ModelDefinition,
    ) -> ModelDefinition:
        """
        Try to fetch model definition from storage and deep merge with base definition.
        Falls back to base definition on failure.
        """
        try:
            override_dict = await self._deployment_repository.fetch_model_definition(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                model_definition_path=model_revision.mounts.model_definition_path,
            )
            base_dict = base_definition.model_dump(exclude_none=True, by_alias=True)
            merged_dict = deep_merge(base_dict, override_dict)
            merged_definition = ModelDefinition.model_validate(merged_dict)
            log.debug(
                "Model definition override applied successfully for vfolder {}",
                model_revision.mounts.model_vfolder_id,
            )
            return merged_definition
        except DefinitionFileNotFound:
            log.debug(
                "Model definition override file not found for vfolder {}, "
                "using generated definition",
                model_revision.mounts.model_vfolder_id,
            )
            return base_definition
        except Exception:
            log.warning(
                "Failed to apply model definition override for vfolder {}, "
                "using generated definition",
                model_revision.mounts.model_vfolder_id,
                exc_info=True,
            )
            return base_definition
