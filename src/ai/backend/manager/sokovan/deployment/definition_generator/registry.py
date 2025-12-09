from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import RuntimeVariant
from ai.backend.common.utils import deep_merge
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.cmd import (
    CMDModelDefinitionGenerator,
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


@dataclass
class RegistryArgs:
    deployment_repository: DeploymentRepository


class ModelDefinitionGeneratorRegistry:
    """
    Registry for generating model definitions.

    For all runtime variants:
    1. Generate base definition from variant-specific default generator
    2. If model-definition.yml exists, merge it with base (file overrides base)
    3. For CUSTOM variant without model-definition.yml, raise error
    """

    _deployment_repository: DeploymentRepository
    _default_generators: dict[
        RuntimeVariant,
        CMDModelDefinitionGenerator
        | VLLMModelDefinitionGenerator
        | HuggingFaceTGIModelDefinitionGenerator
        | NIMModelDefinitionGenerator
        | SGLangModelDefinitionGenerator
        | ModularMAXModelDefinitionGenerator,
    ]

    def __init__(self, args: RegistryArgs) -> None:
        self._deployment_repository = args.deployment_repository
        self._default_generators = {
            RuntimeVariant.VLLM: VLLMModelDefinitionGenerator(),
            RuntimeVariant.HUGGINGFACE_TGI: HuggingFaceTGIModelDefinitionGenerator(),
            RuntimeVariant.NIM: NIMModelDefinitionGenerator(),
            RuntimeVariant.SGLANG: SGLangModelDefinitionGenerator(),
            RuntimeVariant.MODULAR_MAX: ModularMAXModelDefinitionGenerator(),
            RuntimeVariant.CMD: CMDModelDefinitionGenerator(),
        }

    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        """
        Generate model definition for the given revision.

        Priority:
        1. Generate base definition from variant-specific default generator
        2. If model-definition.yml exists, merge it with base (file overrides base)
        3. For CUSTOM variant without model-definition.yml, raise error
        """
        runtime_variant = model_revision.execution.runtime_variant

        # Generate base definition from default generator (for non-CUSTOM variants)
        default_generator = self._default_generators.get(runtime_variant)
        if default_generator is not None:
            base_definition = await default_generator.generate_model_definition(model_revision)
            base_dict = base_definition.model_dump(mode="python")
        else:
            # CUSTOM variant has no default generator
            base_dict = {}

        # Try to load model-definition.yml
        try:
            model_definition_from_file = await self._deployment_repository.fetch_model_definition(
                vfolder_id=model_revision.mounts.model_vfolder_id,
                model_definition_path=model_revision.mounts.model_definition_path,
            )
        except DefinitionFileNotFound:
            model_definition_from_file = None

        # Handle CUSTOM variant - model-definition.yml is required
        if runtime_variant == RuntimeVariant.CUSTOM and model_definition_from_file is None:
            raise DefinitionFileNotFound(
                "model-definition.yml is required for CUSTOM runtime variant"
            )

        # Merge: base definition + model-definition.yml (file overrides base)
        if model_definition_from_file is not None:
            merged_dict = deep_merge(base_dict, model_definition_from_file)
        else:
            merged_dict = base_dict

        return ModelDefinition.model_validate(merged_dict)
