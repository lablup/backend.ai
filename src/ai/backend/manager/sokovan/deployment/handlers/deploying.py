"""Handlers for DEPLOYING sub-steps (BEP-1049).

Three DEPLOYING handlers are registered flat in the coordinator's HandlerRegistry
alongside other lifecycle handlers, keyed by ``(lifecycle_type, sub_step)``.
Each handler calls the strategy evaluator and applier directly in ``execute()``.

Sub-step flow::

    PROVISIONING ──(success)──▸ PROGRESSING
         │                           │
         │ (expired/give_up)  ┌──────┴──────┐
         ▼                    ▼              ▼
    ROLLING_BACK         COMPLETED      ROLLING_BACK
         │                    │              │
         │ (success)          │ (success)    │ (success)
         ▼                    ▼              ▼
    ROLLED_BACK             READY       ROLLED_BACK
         │                                   │
         │ (success, via Progressing)         │ (success, via Progressing)
         ▼                                   ▼
       READY                               READY

The evaluator determines sub-step assignments and route mutations;
the applier persists them to DB atomically.  Each handler classifies
deployments into successes (transition forward), errors (failure path),
and skipped (still in progress — no state transition).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentLifecycleStatus,
    DeploymentStatusTransitions,
    DeploymentSubStep,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.applier import (
    StrategyResultApplier,
)
from ai.backend.manager.sokovan.deployment.strategy.evaluator import (
    DeploymentStrategyEvaluator,
)
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# DEPLOYING sub-step handlers
# ---------------------------------------------------------------------------


class DeployingProvisioningHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROVISIONING sub-step.

    New-revision routes are being created; waiting for them to become HEALTHY.
    The evaluator assigns sub-steps; when all new routes are healthy the
    deployment advances to PROGRESSING (success), otherwise it stays in
    PROVISIONING (skipped — no state transition).
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        evaluator: DeploymentStrategyEvaluator,
        applier: StrategyResultApplier,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._evaluator = evaluator
        self._applier = applier

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-provisioning"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

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
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            need_retry=None,
            expired=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
            give_up=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        deployment_infos = [deployment.deployment_info for deployment in deployments]
        deployment_map = {deployment.deployment_info.id: deployment for deployment in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)

        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []

        # Classify by assigned sub_step
        for deployment in deployments:
            endpoint_id = deployment.deployment_info.id
            assigned = summary.assignments.get(endpoint_id)
            if assigned is None:
                # Evaluation error — handled below
                continue
            if assigned == DeploymentSubStep.PROGRESSING:
                # Advanced to PROGRESSING → success (coordinator transitions)
                successes.append(deployment)
            else:
                # Still PROVISIONING → skip (no state transition)
                skipped.append(deployment)

        # Evaluation errors → execution errors
        errors = [
            DeploymentExecutionError(
                deployment_info=deployment_map[evaluation_error.deployment.id],
                reason=evaluation_error.reason,
                error_detail=evaluation_error.reason,
            )
            for evaluation_error in summary.errors
            if evaluation_error.deployment.id in deployment_map
        ]

        return DeploymentExecutionResult(successes=successes, errors=errors, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROVISIONING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingProgressingHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROGRESSING (+ COMPLETED, ROLLED_BACK).

    This single handler processes three sub-steps:

    - **PROGRESSING**: Still replacing routes — re-evaluate next cycle.
    - **COMPLETED**: Applier has swapped revision → returned as success
      → coordinator transitions to READY.
    - **ROLLED_BACK**: Applier has cleared deploying_revision → returned
      as error → coordinator transitions to READY.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        evaluator: DeploymentStrategyEvaluator,
        applier: StrategyResultApplier,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._evaluator = evaluator
        self._applier = applier

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-progressing"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

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
        ready = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_status=None,
        )
        rolling_back = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_status=DeploymentSubStep.ROLLING_BACK,
        )
        return DeploymentStatusTransitions(
            success=ready,
            need_retry=None,
            expired=rolling_back,
            give_up=rolling_back,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        deployment_infos = [deployment.deployment_info for deployment in deployments]
        deployment_map = {deployment.deployment_info.id: deployment for deployment in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)

        # Filter out deployments that have been marked for destruction during DEPLOYING.
        # Without this guard, a COMPLETED sub_step would swap revisions and
        # transition the deployment back to READY, resurrecting it.
        destroying_ids = {
            deployment.deployment_info.id
            for deployment in deployments
            if deployment.deployment_info.state.lifecycle
            in (EndpointLifecycle.DESTROYING, EndpointLifecycle.DESTROYED)
        }
        if destroying_ids:
            log.warning(
                "Skipping {} deployments with DESTROYING/DESTROYED lifecycle during DEPLOYING",
                len(destroying_ids),
            )

        successes: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []
        skipped: list[DeploymentWithHistory] = []

        terminal_ids = apply_result.completed_ids | apply_result.rolled_back_ids
        evaluation_error_ids = {e.deployment.id for e in summary.errors}

        # COMPLETED → successes (coordinator transitions to READY)
        for endpoint_id in apply_result.completed_ids:
            if endpoint_id in destroying_ids:
                continue
            deployment = deployment_map.get(endpoint_id)
            if deployment is not None:
                successes.append(deployment)

        # ROLLED_BACK → errors (coordinator transitions to READY)
        for endpoint_id in apply_result.rolled_back_ids:
            if endpoint_id in destroying_ids:
                continue
            deployment = deployment_map.get(endpoint_id)
            if deployment is not None:
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Deployment rolled back — all new routes failed",
                        error_detail="Strategy FSM determined rollback",
                    )
                )

        # Evaluation errors → execution errors
        for error_data in summary.errors:
            deployment = deployment_map.get(error_data.deployment.id)
            if deployment is not None:
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=error_data.reason,
                        error_detail=error_data.reason,
                    )
                )

        # Still PROGRESSING → skipped (no state transition)
        for deployment in deployments:
            endpoint_id = deployment.deployment_info.id
            if (
                endpoint_id not in terminal_ids
                and endpoint_id not in destroying_ids
                and endpoint_id not in evaluation_error_ids
            ):
                skipped.append(deployment)

        return DeploymentExecutionResult(successes=successes, errors=errors, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROGRESSING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingRollingBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLING_BACK sub-step.

    Actively rolling back failed new-revision routes to the previous revision.
    The evaluator re-evaluates the deployment (which is now in ROLLING_BACK)
    and the applier drains new-revision routes and restores old-revision routes.
    Once rollback is complete, the evaluator assigns ROLLED_BACK, which the
    ProgressingHandler will pick up and transition to READY.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        evaluator: DeploymentStrategyEvaluator,
        applier: StrategyResultApplier,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._evaluator = evaluator
        self._applier = applier

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-rolling-back"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            )
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
            need_retry=None,
            expired=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
            give_up=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        deployment_infos = [deployment.deployment_info for deployment in deployments]
        deployment_map = {deployment.deployment_info.id: deployment for deployment in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)

        # Successfully evaluated deployments → successes (coordinator transitions to ROLLED_BACK)
        evaluated_ids = set(summary.assignments.keys())
        successes = [
            deployment
            for deployment in deployments
            if deployment.deployment_info.id in evaluated_ids
        ]

        # Evaluation errors → execution errors
        errors = [
            DeploymentExecutionError(
                deployment_info=deployment_map[evaluation_error.deployment.id],
                reason=evaluation_error.reason,
                error_detail=evaluation_error.reason,
            )
            for evaluation_error in summary.errors
            if evaluation_error.deployment.id in deployment_map
        ]

        return DeploymentExecutionResult(successes=successes, errors=errors)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.ROLLING_BACK
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
