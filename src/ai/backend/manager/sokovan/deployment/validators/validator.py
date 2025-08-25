from abc import ABC
from typing import Optional

from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.repositories.deployment.preparation_types import DeploymentPreparationData
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition


class DeploymentValidateRule(ABC):
    async def validate(
        self,
        spec: DeploymentCreator,
        prep_data: DeploymentPreparationData,
        service_definition: Optional[ModelServiceDefinition] = None,
    ) -> None:
        raise NotImplementedError("Subclasses must implement this method")


class DeploymentValidator:
    _rules: list[DeploymentValidateRule]

    def __init__(self, rules: list[DeploymentValidateRule]) -> None:
        self._rules = rules

    async def validate(
        self,
        spec: DeploymentCreator,
        prep_data: DeploymentPreparationData,
        service_definition: Optional[ModelServiceDefinition] = None,
    ) -> None:
        for rule in self._rules:
            await rule.validate(spec, prep_data, service_definition)
