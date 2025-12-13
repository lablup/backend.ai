"""Handler for reconciling ready deployments with mismatched replica counts."""

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


class ReconcileDeploymentHandler(DeploymentHandler):
    """Handler for checking ready state deployments and reconciling their status."""

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
    ) -> None:
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "reconcile-deployments"

    @property
    def lock_id(self) -> Optional[LockID]:
        """
        Lock for reconciling deployments.
        Returns None because this operation does not run in short intervals.
        """
        return None

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler."""
        return [EndpointLifecycle.READY]

    @classmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after this handler's operation."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        return EndpointLifecycle.SCALING

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Check ready deployments."""
        log.debug("Checking ready deployments for replica-route mismatches")

        return await self._deployment_executor.check_ready_deployments_that_need_scaling(
            deployments
        )

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after checking ready deployments."""
        log.debug("Post-processing after checking ready deployments")
        if result.errors:
            await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.SCALING)
