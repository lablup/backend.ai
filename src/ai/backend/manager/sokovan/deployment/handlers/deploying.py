"""Handlers for DEPLOYING sub-steps (BEP-1049).

All sub-step handlers are registered flat in the coordinator alongside other
lifecycle handlers.  The coordinator dispatches by sub-step using the
``(lifecycle_type, sub_step)`` registry key.

Each handler calls the strategy evaluator in ``execute()`` to evaluate
the deployment FSM, then uses ``StrategyResultApplier`` to persist
sub_step assignments and route mutations.
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
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.applier import StrategyResultApplier
from ai.backend.manager.sokovan.deployment.strategy.evaluator import DeploymentStrategyEvaluator
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# DEPLOYING sub-step handlers
# ---------------------------------------------------------------------------


class DeployingProvisioningHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROVISIONING sub-step.

    New-revision routes are being created; waiting for them to become HEALTHY.
    execute() evaluates strategy FSM and applies route mutations via applier.
    post_process() re-schedules the DEPLOYING/PROVISIONING cycle and triggers route provisioning.
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
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
        )

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        summary = await self._evaluator.evaluate(deployments)
        await self._applier.apply(summary)

        # Deployments that were successfully evaluated stay in DEPLOYING;
        # those that failed evaluation are reported as errors.
        evaluated_ids = set(summary.assignments.keys())
        successes = [d for d in deployments if d.id in evaluated_ids]
        errors = [
            DeploymentExecutionError(
                deployment_info=e.deployment,
                reason=f"Strategy evaluation failed: {e.reason}",
                error_detail=e.reason,
            )
            for e in summary.errors
        ]
        return DeploymentExecutionResult(successes=successes, errors=errors)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROVISIONING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingProgressingHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROGRESSING sub-step (including terminal states).

    Handles three sub-steps determined by strategy evaluation:

    - **PROGRESSING**: Actively replacing routes — no-op, re-schedule next cycle.
    - **COMPLETED**: All strategy conditions met — applier swaps revision → success (→ READY).
    - **ROLLED_BACK**: All new routes failed — applier clears deploying_revision → failure (→ READY).
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
        ready = DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY)
        return DeploymentStatusTransitions(
            success=ready,
            failure=ready,
        )

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        summary = await self._evaluator.evaluate(deployments)
        apply_result = await self._applier.apply(summary)

        deployment_map = {d.id: d for d in deployments}

        completed = [
            deployment_map[eid] for eid in apply_result.completed_ids if eid in deployment_map
        ]
        rolled_back = [
            deployment_map[eid] for eid in apply_result.rolled_back_ids if eid in deployment_map
        ]

        errors: list[DeploymentExecutionError] = [
            DeploymentExecutionError(
                deployment_info=deployment,
                reason="Deployment rolled back — all new routes failed",
                error_detail="Strategy FSM determined rollback",
            )
            for deployment in rolled_back
        ]
        # Include evaluation errors so they flow through coordinator's
        # failure classification (give_up/expired/need_retry).
        errors.extend(
            DeploymentExecutionError(
                deployment_info=e.deployment,
                reason=f"Strategy evaluation failed: {e.reason}",
                error_detail=e.reason,
            )
            for e in summary.errors
        )

        return DeploymentExecutionResult(
            successes=completed,
            errors=errors,
        )

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        # Re-schedule DEPLOYING for still-progressing deployments
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROGRESSING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
