from __future__ import annotations

import logging
from dataclasses import dataclass

from ai.backend.common.config import ModelDefinition
from ai.backend.common.exception import RuntimeVariantNotSupportedError
from ai.backend.common.types import RuntimeVariant
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.base import (
    ModelDefinitionContext,
    ModelDefinitionGenerator,
)
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

    async def generate_model_definition(self, context: ModelDefinitionContext) -> ModelDefinition:
        """
        Generate the final model definition for a revision.

        Called at revision creation time to produce the fully-resolved definition
        that is stored in the DB. Subsequent PROVISIONING reads the stored value
        directly — no vfolder access at runtime.

        Merge priority (later overrides earlier):
            1. Generator-produced definition (lowest)
            2. Vfolder file override (non-CUSTOM only, requires flag)
            3. User-provided model_definition override (highest)
        """
        runtime_variant = context.execution.runtime_variant
        generator = self.get(runtime_variant)
        definition = await generator.generate_model_definition(context)
        definition = await self._apply_vfolder_override(context, runtime_variant, definition)
        return self._apply_user_override(context, definition)

    async def _apply_vfolder_override(
        self,
        context: ModelDefinitionContext,
        runtime_variant: RuntimeVariant,
        base_definition: ModelDefinition,
    ) -> ModelDefinition:
        """For non-CUSTOM variants, optionally merge the vfolder file on top of
        the generator-produced definition. CUSTOM variants already read from
        vfolder in the generator, so this step is skipped to avoid redundancy."""
        if runtime_variant == RuntimeVariant.CUSTOM or not self._enable_model_definition_override:
            return base_definition
        model_definition_path = context.mounts.model_definition_path
        if not model_definition_path:
            return base_definition
        return await self._try_merge_vfolder_definition(
            context=context,
            base_definition=base_definition,
        )

    def _apply_user_override(
        self,
        context: ModelDefinitionContext,
        base_definition: ModelDefinition,
    ) -> ModelDefinition:
        """Merge user-provided model_definition override if present."""
        if not context.model_definition:
            return base_definition
        try:
            return base_definition.merge(context.model_definition)
        except Exception:
            log.error(
                "Failed to merge user-provided model_definition, using server-generated definition",
                exc_info=True,
            )
            return base_definition

    async def _try_merge_vfolder_definition(
        self,
        context: ModelDefinitionContext,
        base_definition: ModelDefinition,
    ) -> ModelDefinition:
        """
        Try to fetch model definition from vfolder storage and deep merge with base definition.
        Falls back to base definition on failure.
        """
        try:
            vfolder_dict = await self._deployment_repository.fetch_model_definition(
                vfolder_id=context.mounts.model_vfolder_id,
                model_definition_path=context.mounts.model_definition_path,
            )
            merged_definition = base_definition.merge(ModelDefinition.model_validate(vfolder_dict))
            log.debug(
                "Vfolder model definition merged successfully for vfolder {}",
                context.mounts.model_vfolder_id,
            )
            return merged_definition
        except DefinitionFileNotFound:
            log.debug(
                "Model definition file not found in vfolder {}, using generated definition",
                context.mounts.model_vfolder_id,
            )
            return base_definition
        except Exception:
            log.warning(
                "Failed to read model definition from vfolder {}, using generated definition",
                context.mounts.model_vfolder_id,
                exc_info=True,
            )
            return base_definition
