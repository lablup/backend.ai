"""Handler for scaling deployments based on load or schedule."""

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


class ScalingDeploymentHandler(DeploymentHandler):
    """Handler for scaling deployments based on load or schedule."""

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
        return "scaling-deployments"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for scaling deployments."""
        return LockID.LOCKID_DEPLOYMENT_AUTO_SCALER

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler."""
        return [EndpointLifecycle.SCALING]

    @classmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after this handler's operation."""
        return EndpointLifecycle.READY

    @classmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        return None

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Check and execute deployment scaling operations."""
        log.debug("Checking for deployment scaling requirements")

        # Execute scaling logic via executor
        result = await self._deployment_executor.scale_deployment(deployments)
        return result

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after scaling deployments."""
        log.info("Scaled {} deployments", len(result.successes))
        if result.successes:
            # Update route statuses for scaled deployments
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
