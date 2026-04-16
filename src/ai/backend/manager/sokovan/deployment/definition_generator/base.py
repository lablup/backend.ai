from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    MountMetadata,
)


@dataclass(frozen=True)
class ModelDefinitionContext:
    """Lightweight context for model definition generation.

    Contains only the fields that generators actually need,
    avoiding the full ModelRevisionSpec dependency (which requires
    image_identifier and resource_spec that no generator uses).
    """

    mounts: MountMetadata
    execution: ExecutionSpec
    model_definition: ModelDefinitionDraft | None


class ModelDefinitionGenerator(ABC):
    """Abstract base class for generating model definitions.

    Generators emit a ``ModelDefinitionDraft`` so partial overlays from
    multiple sources (preset, vfolder yaml, request override) can be merged
    before being resolved to a strict ``ModelDefinition`` at the persistence
    boundary.
    """

    @abstractmethod
    async def generate_model_definition(
        self, context: ModelDefinitionContext
    ) -> ModelDefinitionDraft:
        """Generate a model definition draft based on the provided context."""
        raise NotImplementedError
