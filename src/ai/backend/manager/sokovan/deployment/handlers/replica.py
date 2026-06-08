"""Handler for checking and managing deployment replicas."""

import logging
from collections.abc import Sequence

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, ScalingState
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentWithHistory,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckReplicaDeploymentHandler(DeploymentHandler):
    """Handler for checking and managing deployment replicas."""

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
        return "check-replica-deployments"

    @classmethod
    def category(cls) -> DeploymentHandlerCategory:
        return DeploymentHandlerCategory.SCALING

    @property
    def lock_id(self) -> LockID | None:
        """Lock for checking replicas."""
        return LockID.LOCKID_DEPLOYMENT_CHECK_REPLICA

    @classmethod
    def target_statuses(cls) -> DeploymentTargetStatuses:
        """Target READY **and** DEPLOYING endpoints whose replica count
        may need adjusting.

        Scaling is not exclusive to the steady-state: an autoscaler
        signal (or a replica shortfall) may arrive while the initial
        rollout is still progressing, so DEPLOYING endpoints are
        eligible too. Operates only on the ``STABLE`` slice so we do
        not re-enter reconciliation on endpoints already being scaled
        by the ``scaling`` handler.
        """
        return DeploymentTargetStatuses(
            lifecycle_stages=[
                EndpointLifecycle.READY,
                EndpointLifecycle.DEPLOYING,
            ],
            scaling_states=[ScalingState.STABLE],
        )

    @classmethod
    def status_transitions(cls) -> DeploymentStatusTransitions:
        """No status transition: this handler only records the deployment's desired replica count.
        The group autoscale reconcile reads that count and scales the serving group."""
        return DeploymentStatusTransitions()

    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        """Record each deployment's desired replica count.

        Skips deployments without a ``current_revision`` — scaling is only meaningful once an
        initial revision has been deployed; those are still in the DEPLOYING rollout."""
        log.debug("Checking deployment replicas")

        scalable = [d for d in deployments if d.deployment_info.current_revision is not None]
        if len(scalable) != len(deployments):
            skipped = len(deployments) - len(scalable)
            log.debug(
                "Skipping {} deployments without a current_revision for replica check",
                skipped,
            )
        if not scalable:
            return DeploymentExecutionResult()

        # Calculate desired replicas and adjust
        return await self._deployment_executor.calculate_desired_replicas(scalable)

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """No follow-up: the group autoscale reconcile picks up the recorded desired count."""
        return
