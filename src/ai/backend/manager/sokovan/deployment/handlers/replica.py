"""Handler for checking and managing deployment replicas."""

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckReplicaDeploymentHandler(DeploymentHandler):
    """Handler for checking and managing deployment replicas."""

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
    ):
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-replica-deployments"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for checking replicas."""
        return LockID.LOCKID_DEPLOYMENT_CHECK_REPLICA

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler."""
        return [EndpointLifecycle.READY]

    @classmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after this handler's operation."""
        return EndpointLifecycle.SCALING

    @classmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        return None

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Check and manage deployment replicas."""
        log.debug("Checking deployment replicas")

        # Calculate desired replicas and adjust
        return await self._deployment_executor.calculate_desired_replicas(deployments)

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after checking replicas."""
        log.debug("Post-processing after checking deployment replicas")
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.SCALING)
