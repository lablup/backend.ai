"""Handler for checking pending deployments."""

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


class CheckPendingDeploymentHandler(DeploymentHandler):
    """Handler for checking pending deployments."""

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
        return "check-pending-deployments"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for checking pending deployments."""
        return LockID.LOCKID_DEPLOYMENT_CHECK_PENDING

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler."""
        return [EndpointLifecycle.PENDING, EndpointLifecycle.CREATED]

    @classmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after this handler's operation."""
        return EndpointLifecycle.SCALING

    @classmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        return None

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Check for pending deployments and process them."""
        log.debug("Checking for pending deployments")

        # Execute deployment check logic via executor
        result = await self._deployment_executor.check_pending_deployments(deployments)
        return result

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after checking pending deployments."""
        log.info("Processed {} pending deployments", len(result.successes))
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.SCALING)
