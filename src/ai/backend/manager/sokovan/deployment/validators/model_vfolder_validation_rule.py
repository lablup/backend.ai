"""Model vfolder validation rule for deployment."""

from typing import Optional

from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.repositories.deployment.preparation_types import DeploymentPreparationData
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition
from ai.backend.manager.sokovan.deployment.exceptions import InvalidVFolderOwnership
from ai.backend.manager.sokovan.deployment.validators.validator import DeploymentValidateRule


class ModelVFolderValidationRule(DeploymentValidateRule):
    """Validates model vfolder ownership type."""

    async def validate(
        self,
        spec: DeploymentCreator,
        prep_data: DeploymentPreparationData,
        service_definition: Optional[ModelServiceDefinition] = None,
    ) -> None:
        """Validate model vfolder ownership.

        Raises:
            InvalidVFolderOwnership: If vfolder has group ownership (not user ownership)
        """
        # Check if vfolder has valid ownership type (should be user, not group)
        if prep_data.vfolder_info.ownership_type == VFolderOwnershipType.GROUP:
            raise InvalidVFolderOwnership("Cannot use group type vfolder as model")
