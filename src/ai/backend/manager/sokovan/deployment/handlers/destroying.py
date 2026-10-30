"""Handler for destroying deployments."""

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentWithHistory,
)

from .base import DeploymentHandler

log = StructuredLogger(logging.getLogger(__name__))


class DestroyingDeploymentHandler(DeploymentHandler):
    """Handler for destroying deployments."""

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @classmethod
    @override
    def name(cls) -> str:
        """Get the name of the handler."""
        return "destroying-deployments"

    @classmethod
    @override
    def category(cls) -> DeploymentHandlerCategory:
        return DeploymentHandlerCategory.LIFECYCLE

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Lock for destroying deployments."""
        return LockID.LOCKID_DEPLOYMENT_DESTROYING

    @classmethod
    @override
    def target_statuses(cls) -> DeploymentTargetStatuses:
        """Get the target deployment statuses for this handler."""
        return DeploymentTargetStatuses(lifecycle_stages=[EndpointLifecycle.DESTROYING])

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        """Define state transitions for destroying deployment handler (BEP-1030).

        - success: Deployment → DESTROYED
        - failure (all): Deployment → DESTROYED (always proceed to destroyed)
        """
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.DESTROYED),
            need_retry=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.DESTROYED),
            expired=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.DESTROYED),
            give_up=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.DESTROYED),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        """Process deployments marked for destruction."""
        # Execute destruction logic via executor
        return await self._deployment_executor.destroy_deployment(deployments)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after destroying deployments."""
        log.debug("deployments destroyed", deployment_count=len(result.successes))
        if result.successes:
            # Clean up routes associated with destroyed deployments
            # (draining is the first stage of the termination pipeline)
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.DRAINING)
