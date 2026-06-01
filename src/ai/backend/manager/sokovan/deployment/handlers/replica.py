"""Handler for checking and managing deployment replicas."""

import logging
from collections.abc import Sequence

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, ScalingState
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
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
        """Define state transitions for check replica deployment handler.

        - success: ``scaling_state=SCALING`` only — lifecycle axis is
          preserved so a DEPLOYING endpoint remains DEPLOYING while the
          scaling handler picks up its replica adjustment.
        - failure: None (stays in current state for all failure categories).
        """
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(scaling_state=ScalingState.SCALING),
        )

    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        """Check and manage deployment replicas.

        Skips deployments without a ``current_revision_id`` — scaling is
        only meaningful once an initial revision has been deployed.
        Those endpoints are still in the initial rollout handled by the
        DEPLOYING lifecycle; flipping them into ``scaling_state=SCALING``
        here would misclassify initial provisioning as scaling work.
        """
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

    async def post_process(self, _result: DeploymentExecutionResult) -> None:
        """Handle post-processing after checking replicas."""
        log.debug("Post-processing after checking deployment replicas")
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.SCALING)
