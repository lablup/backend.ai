"""Handlers for DEPLOYING sub-steps (BEP-1049).

Three DEPLOYING handlers are registered flat in the coordinator's HandlerRegistry
alongside other lifecycle handlers, keyed by ``(lifecycle_type, sub_step)``.
Each handler calls the strategy evaluator and applier directly in ``execute()``.

Sub-step flow::

    PROVISIONING ──(evaluator assigns PROGRESSING)──▸ PROGRESSING
         │                                                │
         │ (expired/give_up)                       ┌──────┴──────┐
         ▼                                         ▼              ▼
    ROLLING_BACK ────────────────────────▸    COMPLETED      ROLLING_BACK
         │                                        │              │
         ▼                                        ▼              ▼
    ROLLED_BACK                                 READY       ROLLED_BACK
         │                                                       │
         ▼                                                       ▼
       READY                                                   READY

The evaluator determines sub-step assignments and route mutations;
the applier persists them to DB atomically.  ``status_transitions().success``
keeps the deployment in its current sub-step — actual sub-step advancement
is handled by the applier writing to the ``sub_step`` column.
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
    The evaluator assigns sub-steps (may advance to PROGRESSING); the applier
    writes the assignments to DB.  This handler's ``status_transitions().success``
    keeps the lifecycle at DEPLOYING/PROVISIONING — sub-step advancement is
    handled by the applier.
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
        deployment_infos = [d.deployment_info for d in deployments]
        deployment_map = {d.deployment_info.id: d for d in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)

        # Successfully evaluated deployments → successes
        evaluated_ids = set(summary.assignments.keys())
        successes = [d for d in deployments if d.deployment_info.id in evaluated_ids]

        # Evaluation errors → execution errors
        errors = [
            DeploymentExecutionError(
                deployment_info=deployment_map[e.deployment.id],
                reason=e.reason,
                error_detail=e.reason,
            )
            for e in summary.errors
            if e.deployment.id in deployment_map
        ]

        return DeploymentExecutionResult(successes=successes, errors=errors)

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
        ready = DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY)
        return DeploymentStatusTransitions(
            success=ready,
            need_retry=ready,
            expired=ready,
            give_up=ready,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        deployment_infos = [d.deployment_info for d in deployments]
        deployment_map = {d.deployment_info.id: d for d in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)

        # Filter out deployments that have been marked for destruction during DEPLOYING.
        # Without this guard, a COMPLETED sub_step would swap revisions and
        # transition the deployment back to READY, resurrecting it.
        destroying_ids = {
            d.deployment_info.id
            for d in deployments
            if d.deployment_info.state.lifecycle
            in (EndpointLifecycle.DESTROYING, EndpointLifecycle.DESTROYED)
        }
        if destroying_ids:
            log.warning(
                "Skipping {} deployments with DESTROYING/DESTROYED lifecycle during DEPLOYING",
                len(destroying_ids),
            )

        successes: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []

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

        return DeploymentExecutionResult(successes=successes, errors=errors)

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
                sub_status=DeploymentSubStep.ROLLING_BACK,
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
        deployment_infos = [d.deployment_info for d in deployments]
        deployment_map = {d.deployment_info.id: d for d in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)

        # Successfully evaluated deployments → successes (stay in ROLLING_BACK)
        evaluated_ids = set(summary.assignments.keys())
        successes = [d for d in deployments if d.deployment_info.id in evaluated_ids]

        # Evaluation errors → execution errors
        errors = [
            DeploymentExecutionError(
                deployment_info=deployment_map[e.deployment.id],
                reason=e.reason,
                error_detail=e.reason,
            )
            for e in summary.errors
            if e.deployment.id in deployment_map
        ]

        return DeploymentExecutionResult(successes=successes, errors=errors)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.ROLLING_BACK
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
