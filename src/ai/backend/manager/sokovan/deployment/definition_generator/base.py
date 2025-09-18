from abc import ABC, abstractmethod
from typing import TypeVar

from ai.backend.common.config import ModelDefinition
from ai.backend.manager.data.deployment.types import (
    ModelRevisionSpec,
)

TDefinition = TypeVar("TDefinition")


class ModelDefinitionGenerator(ABC):
    """Abstract base class for generating model definitions."""

    @abstractmethod
    async def generate_definition(self, model_revision: ModelRevisionSpec) -> ModelDefinition:
        """Generate a model definition based on the provided revision (RuntimeVariant)."""
        raise NotImplementedError

    @abstractmethod
    async def validate_configuration(self, config: dict) -> None:
        """Validate the provided model configuration."""
        raise NotImplementedError

    @abstractmethod
    async def override_service_definition(
        self, model_revision: ModelRevisionSpec
    ) -> ModelRevisionSpec:
        """Apply overrides to the model revision based on the service definition."""
        raise NotImplementedError
