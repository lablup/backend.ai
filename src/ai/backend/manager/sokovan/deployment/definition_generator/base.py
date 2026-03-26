from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.config import ModelDefinition
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
    model_definition: ModelDefinition | None


class ModelDefinitionGenerator(ABC):
    """Abstract base class for generating model definitions."""

    @abstractmethod
    async def generate_model_definition(self, context: ModelDefinitionContext) -> ModelDefinition:
        """Generate a model definition based on the provided context."""
        raise NotImplementedError
