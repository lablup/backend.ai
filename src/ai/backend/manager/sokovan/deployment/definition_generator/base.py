from abc import ABC, abstractmethod

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.data.deployment.types import (
    ModelRevisionSpec,
    RequestedModelRevisionSpec,
)


class ModelDefinitionGenerator(ABC):
    """Abstract base class for generating model definitions."""

    @abstractmethod
    async def generate_model_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        """Generate a model definition based on the provided revision (RuntimeVariant)."""
        raise NotImplementedError

    @abstractmethod
    async def generate_model_revision(
        self, requested_model_revision: RequestedModelRevisionSpec
    ) -> ModelRevisionSpec:
        raise NotImplementedError
