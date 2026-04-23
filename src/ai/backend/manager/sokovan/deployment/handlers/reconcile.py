"""Handler for reconciling ready deployments with mismatched replica counts."""

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

    @classmethod
    def category(cls) -> DeploymentHandlerCategory:
        return DeploymentHandlerCategory.SCALING

    @property
    def lock_id(self) -> LockID | None:
        """
        Lock for reconciling deployments.
        Returns None because this operation does not run in short intervals.
        """
        return None

    @classmethod
    def target_statuses(cls) -> DeploymentTargetStatuses:
        """Target READY **and** DEPLOYING endpoints that are not already
        being scaled.

        Replica-route drift can occur during the initial rollout too
        (e.g. a kernel died mid-provisioning), so DEPLOYING endpoints
        are eligible. Operates only on the ``STABLE`` slice so we do
        not compete with an in-flight scaling cycle.
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
        """Define state transitions for reconcile deployment handler.

        Transitions only move the scaling axis; the endpoint's lifecycle
        is preserved so DEPLOYING endpoints remain DEPLOYING.

        - success: None (no drift detected; both axes stay).
        - need_retry, expired, give_up: ``scaling_state=SCALING``
          (mismatch detected — hand off to the scaling handler).
        """
        scaling_in_progress = DeploymentLifecycleStatus(scaling_state=ScalingState.SCALING)
        return DeploymentStatusTransitions(
            success=None,
            need_retry=scaling_in_progress,
            expired=scaling_in_progress,
            give_up=scaling_in_progress,
        )

    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        """Check ready deployments."""
        log.debug("Checking ready deployments for replica-route mismatches")

        return await self._deployment_executor.check_ready_deployments_that_need_scaling(
            deployments
        )

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after checking ready deployments."""
        log.debug("Post-processing after checking ready deployments")
        if result.failures:
            await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.SCALING)
