"""Endpoint name validation rule for deployment."""

from typing import Optional

from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.repositories.deployment.preparation_types import DeploymentPreparationData
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition
from ai.backend.manager.sokovan.deployment.exceptions import DuplicateEndpointName
from ai.backend.manager.sokovan.deployment.validators.validator import DeploymentValidateRule


class EndpointNameValidationRule(DeploymentValidateRule):
    """Validates endpoint name uniqueness."""

    async def validate(
        self,
        spec: DeploymentCreator,
        prep_data: DeploymentPreparationData,
        service_definition: Optional[ModelServiceDefinition] = None,
    ) -> None:
        """Validate endpoint name is unique.

        Raises:
            DuplicateEndpointName: If endpoint name already exists
        """
        if not prep_data.is_endpoint_name_unique:
            raise DuplicateEndpointName(f"Endpoint name '{spec.metadata.name}' already exists")
