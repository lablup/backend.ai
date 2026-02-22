"""Handler for rolling update deployments."""

import logging
from collections.abc import Sequence

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentStatusTransitions
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class RollingUpdateDeploymentHandler(DeploymentHandler):
    """Handler for rolling update deployments (DEPLOYING state).

    Gradually replaces old-revision routes with new-revision routes,
    controlled by max_surge and max_unavailable parameters from the
    deployment policy.

    Each cycle creates new-revision routes and terminates old-revision
    routes within the configured limits. Completed deployments transition
    to READY, while in-progress deployments stay in DEPLOYING for
    the next cycle.
    """

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
    def name(cls) -> str:
        return "rolling-update-deployments"

    @property
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_ROLLING_UPDATE

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    def next_status(cls) -> EndpointLifecycle | None:
        # Only applied to 'successes' (completed rolling updates)
        return EndpointLifecycle.READY

    @classmethod
    def failure_status(cls) -> EndpointLifecycle | None:
        # Stays in DEPLOYING for retry on failure
        return None

    @classmethod
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=EndpointLifecycle.READY,
            failure=None,
        )

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        log.debug("Executing rolling update cycle for {} deployments", len(deployments))
        return await self._deployment_executor.execute_rolling_update_cycle(deployments)

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            log.info(
                "Rolling update completed for {} deployments",
                len(result.successes),
            )
            # Trigger provisioning for newly created routes
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
        if result.skipped:
            log.debug(
                "Rolling update in progress for {} deployments, scheduling next cycle",
                len(result.skipped),
            )
            # Re-mark ROLLING_UPDATE to trigger the next cycle
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.ROLLING_UPDATE
            )
            # Also trigger provisioning for any newly created routes in this cycle
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
