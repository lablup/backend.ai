"""Handlers for DEPLOYING sub-steps (BEP-1049).

In-progress handlers (PROVISIONING, PROGRESSING) run *after* the coordinator
has applied route mutations from the evaluation result.  Their ``execute``
simply returns success.  ``post_process`` triggers the next DEPLOYING cycle
and route provisioning.

The rolled-back handler clears ``deploying_revision`` and transitions the
deployment back to READY.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleStatus,
    DeploymentStatusTransitions,
    DeploymentSubStep,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# In-progress handlers (PROVISIONING / PROGRESSING)
# ---------------------------------------------------------------------------


class DeployingInProgressHandler(DeploymentHandler):
    """Base handler for in-progress DEPLOYING sub-steps.

    execute() returns success for all supplied deployments.
    post_process() re-schedules the DEPLOYING cycle and triggers route provisioning.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-in-progress"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return None  # Lock is managed by the coordinator's _process_with_evaluator

    @classmethod
    @override
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        # Stay in DEPLOYING — no automatic transition here.
        return DeploymentStatusTransitions(success=None, failure=None)

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        # Re-schedule DEPLOYING for the next coordinator cycle
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.DEPLOYING)
        # Trigger route provisioning so new routes get sessions
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingProvisioningHandler(DeployingInProgressHandler):
    """Handler for DEPLOYING / PROVISIONING sub-step.

    New-revision routes are being created; waiting for them to become HEALTHY.
    """

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-provisioning"

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
            failure=None,
        )


class DeployingProgressingHandler(DeployingInProgressHandler):
    """Handler for DEPLOYING / PROGRESSING sub-step.

    Actively replacing old routes with new routes.
    """

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-progressing"

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            failure=None,
        )


# ---------------------------------------------------------------------------
# Rolled-back handler
# ---------------------------------------------------------------------------


class DeployingRolledBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLED_BACK sub-step.

    Clears ``deploying_revision`` and transitions to READY / ROLLED_BACK.
    """

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-rolled-back"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return None  # Lock is managed by the coordinator

    @classmethod
    @override
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
            failure=None,
        )

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        endpoint_ids = {d.id for d in deployments}
        await self._deployment_repo.clear_deploying_revision(endpoint_ids)
        log.info("Cleared deploying_revision for {} rolled-back deployments", len(endpoint_ids))
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        pass
