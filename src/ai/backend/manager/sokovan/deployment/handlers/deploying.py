"""Handlers for DEPLOYING sub-steps (BEP-1049).

All sub-step handlers are registered flat in the coordinator alongside other
lifecycle handlers.  The coordinator dispatches by sub-step using the
``(lifecycle_type, sub_step)`` registry key.

Before the sub-step handlers run, the coordinator executes
``DeployingEvaluatePreStep`` to evaluate the strategy FSM, update the
``sub_step`` column, and apply route mutations.
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
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import (
    RouteBatchUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.evaluator import DeploymentStrategyEvaluator
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# Evaluate pre-step (runs before sub-step handlers)
# ---------------------------------------------------------------------------


class DeployingEvaluatePreStep:
    """Evaluates strategy for all DEPLOYING deployments.

    This is NOT a handler.  The coordinator runs it once before dispatching
    to individual sub-step handlers.

    - Updates the ``sub_step`` column in DB (including COMPLETED/ROLLED_BACK).
    - Applies route mutations (rollout / drain).
    """

    def __init__(
        self,
        evaluator: DeploymentStrategyEvaluator,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._evaluator = evaluator
        self._deployment_repo = deployment_repo

    async def run(self) -> None:
        """Run evaluation and apply side-effects (sub_step update + route changes).

        Sub-step updates and route mutations are applied in a single transaction
        via ``apply_deploying_pre_step`` to prevent inconsistent state where
        sub_step is updated (e.g. COMPLETED) but route creation fails.
        """
        deployments = await self._deployment_repo.get_endpoints_by_statuses([
            EndpointLifecycle.DEPLOYING
        ])
        if not deployments:
            return
        log.info("pre-step evaluate: processing {} deployments", len(deployments))
        deployment_ids = [d.id for d in deployments]
        with DeploymentRecorderContext.scope("deploying-pre-step", entity_ids=deployment_ids):
            eval_result = await self._evaluator.evaluate(deployments)

        changes = eval_result.route_changes
        drain: BatchUpdater[RoutingRow] | None = None
        if changes.drain_route_ids:
            drain = BatchUpdater(
                spec=RouteBatchUpdaterSpec(
                    status=RouteStatus.TERMINATING,
                    traffic_ratio=0.0,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                ),
                conditions=[RouteConditions.by_ids(changes.drain_route_ids)],
            )

        # Apply sub_step updates and route mutations atomically
        if eval_result.assignments or changes.rollout_specs or drain:
            await self._deployment_repo.apply_deploying_pre_step(
                eval_result.assignments,
                changes.rollout_specs,
                drain,
            )
            log.debug(
                "Applied pre-step: {} sub_step groups, {} routes created, {} routes drained",
                len(eval_result.assignments),
                len(changes.rollout_specs),
                len(changes.drain_route_ids),
            )


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
        return None

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.DEPLOYING)]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        # Stay in DEPLOYING — no transition.
        return DeploymentStatusTransitions()

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
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            )
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
        )


class DeployingProgressingHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROGRESSING sub-step (including terminal states).

    Handles three sub-steps set by the pre-step evaluator:

    - **PROGRESSING**: Actively replacing routes — no-op, re-schedule next cycle.
    - **COMPLETED**: All strategy conditions met — revision swap → success (→ READY).
    - **ROLLED_BACK**: All new routes failed — clear deploying_revision → failure (→ READY).
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-progressing"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return None

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.COMPLETED,
            ),
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        ready = DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY)
        return DeploymentStatusTransitions(
            success=ready,
            need_retry=ready,
            expired=ready,
            give_up=ready,
        )

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        completed: list[DeploymentInfo] = []
        rolled_back: list[DeploymentInfo] = []

        for deployment in deployments:
            # Skip deployments that have been marked for destruction during DEPLOYING.
            # Without this guard, a COMPLETED sub_step would swap revisions and
            # transition the deployment back to READY, resurrecting it.
            if deployment.state.lifecycle in (
                EndpointLifecycle.DESTROYING,
                EndpointLifecycle.DESTROYED,
            ):
                log.warning(
                    "deployment {}: skipping — lifecycle is {} during DEPLOYING",
                    deployment.id,
                    deployment.state.lifecycle,
                )
                continue

            match deployment.sub_step:
                case DeploymentSubStep.COMPLETED:
                    completed.append(deployment)
                case DeploymentSubStep.ROLLED_BACK:
                    rolled_back.append(deployment)
                case _:
                    # PROVISIONING / PROGRESSING: still in progress — intentionally
                    # excluded from successes/errors so no lifecycle transition occurs.
                    # The next coordinator cycle will re-evaluate via the pre-step.
                    pass

        if completed:
            endpoint_ids = {deployment.id for deployment in completed}
            swapped = await self._deployment_repo.complete_deployment_revision_swap(endpoint_ids)
            log.info(
                "Swapped revision for {}/{} completed deployments",
                swapped,
                len(endpoint_ids),
            )

        if rolled_back:
            endpoint_ids = {deployment.id for deployment in rolled_back}
            await self._deployment_repo.clear_deploying_revision(endpoint_ids)
            log.info("Cleared deploying_revision for {} rolled-back deployments", len(endpoint_ids))

        return DeploymentExecutionResult(
            successes=completed,
            errors=[
                DeploymentExecutionError(
                    deployment_info=deployment,
                    reason="Deployment rolled back — all new routes failed",
                    error_detail="Strategy FSM determined rollback",
                )
                for deployment in rolled_back
            ],
        )

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        # Re-schedule DEPLOYING for still-progressing deployments
        await self._deployment_controller.mark_lifecycle_needed(DeploymentLifecycleType.DEPLOYING)
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
