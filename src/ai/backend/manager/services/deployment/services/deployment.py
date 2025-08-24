from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ReplicaSpec,
)
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
        # Fetch deployment from repository
        # For now, return a placeholder
        # TODO: Fetch actual deployment from repository
        deployment_info = DeploymentInfo(
            id=action.deployment_id,
            metadata=DeploymentMetadata(
                name="placeholder",
                domain="default",
                project=action.deployment_id,  # placeholder
                resource_group="default",
                created_user=action.deployment_id,  # placeholder
                session_owner=action.deployment_id,  # placeholder
            ),
            replica_spec=ReplicaSpec(replica_count=1),
            network=DeploymentNetworkSpec(open_to_public=False),
            model_revisions=[],
        )

        return GetDeploymentInfoActionResult(deployment=deployment_info)

    async def list(self, action: ListDeploymentsAction) -> ListDeploymentsActionResult:
        """List deployments for a user."""
        # Query deployments from repository
        # For now, return empty list
        deployments: list[DeploymentInfo] = []

        # TODO: Implement actual list logic using repository
        # deployments = await self._deployment_repository.list_deployments(
        #     session_owner_id=action.session_owner_id,
        #     name_filter=action.name
        # )

        return ListDeploymentsActionResult(deployments=deployments)

    async def modify(self, action: ModifyDeploymentAction) -> ModifyDeploymentActionResult:
        """Modify deployment metadata, replica spec, or network configuration."""
        # Apply partial updates using the modifier
        action.modifier.fields_to_update()

        # TODO: Apply updates to the deployment
        # This will handle all modifications including scaling, metadata, network, etc.
        # await self._deployment_controller.modify_deployment(
        #     action.deployment_id,
        #     updates
        # )

        # For now, return a placeholder
        deployment_info = DeploymentInfo(
            id=action.deployment_id,
            metadata=DeploymentMetadata(
                name="modified",
                domain="default",
                project=action.deployment_id,
                resource_group="default",
                created_user=action.deployment_id,
                session_owner=action.deployment_id,
            ),
            replica_spec=ReplicaSpec(replica_count=1),
            network=DeploymentNetworkSpec(open_to_public=False),
            model_revisions=[],
        )

        return ModifyDeploymentActionResult(deployment=deployment_info)
