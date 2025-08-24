from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.services.deployment.actions import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
    DeleteDeploymentAction,
    DeleteDeploymentActionResult,
    GetDeploymentInfoAction,
    GetDeploymentInfoActionResult,
    ListDeploymentsAction,
    ListDeploymentsActionResult,
    ModifyDeploymentAction,
    ModifyDeploymentActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment import DeploymentRepository
    from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController


class DeploymentService:
    """Service implementation for deployment operations."""

    _deployment_repository: DeploymentRepository
    _deployment_controller: DeploymentController

    def __init__(
        self,
        deployment_repository: DeploymentRepository,
        deployment_controller: DeploymentController,
    ) -> None:
        self._deployment_repository = deployment_repository
        self._deployment_controller = deployment_controller

    async def create(self, action: CreateDeploymentAction) -> CreateDeploymentActionResult:
        """Create a new deployment."""
        # Use deployment_controller to create the deployment
        deployment_info = await self._deployment_controller.create_deployment(action.creator)

        return CreateDeploymentActionResult(deployment=deployment_info)

    async def delete(self, action: DeleteDeploymentAction) -> DeleteDeploymentActionResult:
        """Delete an existing deployment."""
        # Use deployment_controller to delete the deployment
        await self._deployment_controller.delete_model_service(action.deployment_id)

        return DeleteDeploymentActionResult(deployment_id=action.deployment_id)

    async def get_info(self, action: GetDeploymentInfoAction) -> GetDeploymentInfoActionResult:
        """Get deployment information."""
        deployment = await self._deployment_repository.get_endpoint_info(action.deployment_id)
        return GetDeploymentInfoActionResult(deployment=deployment)

    async def list(self, action: ListDeploymentsAction) -> ListDeploymentsActionResult:
        """List deployments for a user."""
        deployments = await self._deployment_repository.list_endpoints_by_owner(
            owner_id=action.session_owner_id, name=action.name
        )
        return ListDeploymentsActionResult(deployments=deployments)

    async def modify(self, action: ModifyDeploymentAction) -> ModifyDeploymentActionResult:
        """Modify deployment metadata, replica spec, or network configuration."""
        # Use deployment controller to handle all updates
        deployment_info = await self._deployment_controller.update_deployment(
            action.deployment_id, action.modifier
        )

        return ModifyDeploymentActionResult(deployment=deployment_info)
