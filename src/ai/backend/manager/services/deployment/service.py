from datetime import datetime
from uuid import uuid4

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
    CreateDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
    DestroyDeploymentActionResult,
)
from ai.backend.manager.services.deployment.actions.list_deployments import (
    ListDeploymentsAction,
    ListDeploymentsActionResult,
)
from ai.backend.manager.services.deployment.actions.list_model_revisions import (
    ListModelRevisionsAction,
    ListModelRevisionsActionResult,
)
from ai.backend.manager.services.deployment.actions.list_replicas import (
    ListModelReplicasAction,
    ListModelReplicasActionResult,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import (
    SyncReplicaAction,
    SyncReplicaActionResult,
)
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController


class DeploymentService:
    def __init__(self, deployment_controller: DeploymentController) -> None:
        """Initialize deployment service with controller."""
        self._deployment_controller = deployment_controller

    async def create(self, action: CreateDeploymentAction) -> CreateDeploymentActionResult:
        return CreateDeploymentActionResult(
            data=DeploymentInfo(
                id=uuid4(),
                metadata=DeploymentMetadata(
                    name="test",
                    domain="default",
                    project=uuid4(),
                    resource_group="default",
                    created_user=uuid4(),
                    session_owner=uuid4(),
                    created_at=datetime.now(),
                ),
                state=DeploymentState(lifecycle=EndpointLifecycle.CREATED, retry_count=0),
                replica_spec=ReplicaSpec(replica_count=1),
                network=DeploymentNetworkSpec(
                    open_to_public=True,
                ),
                model_revisions=[],
            )
        )

    async def destroy(self, action: DestroyDeploymentAction) -> DestroyDeploymentActionResult:
        return DestroyDeploymentActionResult(success=True)

    async def sync_replicas(self, action: SyncReplicaAction) -> SyncReplicaActionResult:
        return SyncReplicaActionResult(success=True)

    async def list_deployments(self, action: ListDeploymentsAction) -> ListDeploymentsActionResult:
        return ListDeploymentsActionResult(data=[], total_count=0)

    async def list_model_revisions(
        self, action: ListModelRevisionsAction
    ) -> ListModelRevisionsActionResult:
        return ListModelRevisionsActionResult(data=[], total_count=0)

    async def list_model_replicas(
        self, action: ListModelReplicasAction
    ) -> ListModelReplicasActionResult:
        return ListModelReplicasActionResult(data=[], total_count=0)
