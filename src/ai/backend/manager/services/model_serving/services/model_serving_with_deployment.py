"""Model serving service with DeploymentController integration example."""

import logging
import uuid
from typing import TYPE_CHECKING

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.types import ServiceInfo

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.deployment import DeploymentController

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelServingServiceWithDeployment:
    """
    Example integration of ModelServingService with DeploymentController.

    This shows how the existing model_serving service can delegate
    deployment operations to the sokovan DeploymentController.
    """

    _deployment_controller: "DeploymentController"

    def __init__(
        self,
        deployment_controller: "DeploymentController",
    ) -> None:
        self._deployment_controller = deployment_controller

    async def create(
        self,
        action: CreateModelServiceAction,
    ) -> CreateModelServiceActionResult:
        """
        Create a model service using DeploymentController.

        This method delegates the actual deployment work to the
        DeploymentController while maintaining the existing action interface.
        """
        log.info(
            "Creating model service '{}' via DeploymentController",
            action.creator.service_name,
        )

        # Delegate to DeploymentController
        service_info = await self._deployment_controller.create_model_service(action.creator)

        return CreateModelServiceActionResult(
            data=service_info,
        )

    async def delete(
        self,
        endpoint_id: str,
        force: bool = False,
    ) -> bool:
        """
        Delete a model service using DeploymentController.
        """
        log.info("Deleting model service {} via DeploymentController", endpoint_id)

        # Delegate to DeploymentController
        return await self._deployment_controller.delete_model_service(
            uuid.UUID(endpoint_id),
            force=force,
        )

    async def scale(
        self,
        endpoint_id: str,
        target_replicas: int,
    ) -> ServiceInfo:
        """
        Scale a model service using DeploymentController.
        """
        log.info(
            "Scaling model service {} to {} replicas via DeploymentController",
            endpoint_id,
            target_replicas,
        )

        # Delegate to DeploymentController
        return await self._deployment_controller.scale_model_service(
            uuid.UUID(endpoint_id),
            target_replicas,
        )
