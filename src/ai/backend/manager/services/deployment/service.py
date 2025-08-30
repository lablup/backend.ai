"""Deployment service for managing model deployments."""

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentService:
    """Service for managing deployments."""

    _deployment_controller: DeploymentController

    def __init__(self, deployment_controller: DeploymentController) -> None:
        """Initialize deployment service with controller."""
        self._deployment_controller = deployment_controller

    async def create(self, action: CreateDeploymentAction) -> CreateDeploymentActionResult:
        """Create a new deployment.

        Args:
            action: Create deployment action containing the creator specification

        Returns:
            CreateDeploymentActionResult: Result containing the created deployment info
        """
        log.info("Creating deployment with name: {}", action.creator.name)
        deployment_info = await self._deployment_controller.create_deployment(action.creator)
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.CHECK_PENDING
        )
        return CreateDeploymentActionResult(data=deployment_info)

    async def destroy(self, action: DestroyDeploymentAction) -> DestroyDeploymentActionResult:
        """Destroy an existing deployment.

        Args:
            action: Destroy deployment action containing the endpoint ID

        Returns:
            DestroyDeploymentActionResult: Result indicating success or failure
        """
        log.info("Destroying deployment with ID: {}", action.endpoint_id)
        success = await self._deployment_controller.destroy_deployment(action.endpoint_id)
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.DESTROYING)
        return DestroyDeploymentActionResult(success=success)
