"""Handler for destroying deployments."""

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import DeploymentExecutionResult

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class DestroyingDeploymentHandler(DeploymentHandler):
    """Handler for destroying deployments."""

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ):
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "destroying-deployments"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for destroying deployments."""
        return LockID.LOCKID_DEPLOYMENT_DESTROYING

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler."""
        return [EndpointLifecycle.DESTROYING]

    @classmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after destroying."""
        return EndpointLifecycle.DESTROYED

    @classmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        # No failure status for destroying deployments
        return EndpointLifecycle.DESTROYED

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Process deployments marked for destruction."""
        log.debug("Processing deployments marked for destruction")

        # Execute destruction logic via executor
        return await self._deployment_executor.destroy_deployment(deployments)

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after destroying deployments."""
        log.info("Destroyed {} deployments", len(result.successes))
        if result.successes:
            # Clean up routes associated with destroyed deployments
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.TERMINATING)
