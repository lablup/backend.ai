"""Handlers for DEPLOYING sub-steps (BEP-1049).

Two DEPLOYING handlers are registered in the coordinator's HandlerRegistry:

- **DeployingProvisioningHandler**: Runs the strategy FSM each cycle to
  create/drain routes and check for completion.
- **DeployingRollingBackHandler**: Clears ``deploying_revision`` and
  transitions directly to READY.

Sub-step flow::

    PROVISIONING ──(need_retry)──▸ PROVISIONING  (route mutations, logged)
         │
         │ (success)
         ▼
       READY  (completed — all routes replaced)

    PROVISIONING ──(timeout)──▸ ROLLING_BACK ──(success)──▸ READY

The evaluator determines sub-step assignments and route mutations;
the applier persists them to DB atomically.  Each handler classifies
deployments into successes (transition forward), need_retry (route mutations
with history logged), and skipped (no change — waiting).
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
    """Handler for the DEPLOYING / PROVISIONING sub-step.

    Runs the strategy FSM each cycle to create/drain routes and check
    for completion.  Classification:

    - **Route mutations executed** (create/drain): need_retry — stays in
      PROVISIONING with a new history record for progress tracking.
      Never escalated to give_up (normal progress).
    - **No changes** (routes still warming up): skipped — no history.
    - **Completed** (all old routes replaced): success → READY.
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
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_status=None,
            ),
            need_retry=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        deployment_infos = [d.deployment_info for d in deployments]
        deployment_map = {d.deployment_info.id: d for d in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)

        # Filter out deployments marked for destruction during DEPLOYING.
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
        skipped: list[DeploymentWithHistory] = []
        need_retry: list[DeploymentWithHistory] = []

        # COMPLETED → success (coordinator transitions to READY)
        for endpoint_id in apply_result.completed_ids:
            if endpoint_id in destroying_ids:
                continue
            deployment = deployment_map.get(endpoint_id)
            if deployment is not None:
                successes.append(deployment)

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

        # Classify rest: route mutations happened → need_retry (never give_up),
        # no changes → skipped (no history).
        completed_or_error_ids = apply_result.completed_ids | {
            e.deployment.id for e in summary.errors
        }
        has_route_mutations = bool(apply_result.routes_created or apply_result.routes_drained)
        for deployment in deployments:
            endpoint_id = deployment.deployment_info.id
            if endpoint_id in completed_or_error_ids or endpoint_id in destroying_ids:
                continue
            if has_route_mutations:
                need_retry.append(deployment)
            else:
                skipped.append(deployment)

        return DeploymentExecutionResult(
            successes=successes, errors=errors, skipped=skipped, need_retry=need_retry
        )

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROVISIONING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingRollingBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLING_BACK sub-step.

    Clears ``deploying_revision`` and transitions directly to READY.
    This is a cleanup-only operation — no FSM evaluation needed.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        applier: StrategyResultApplier,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
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
                lifecycle=EndpointLifecycle.READY,
                sub_status=None,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        all_deployment_ids = {deployment.deployment_info.id for deployment in deployments}
        await self._applier.clear_deploying_revision(all_deployment_ids)
        log.info(
            "Cleared deploying_revision for {} rolling-back deployments",
            len(all_deployment_ids),
        )
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.ROLLING_BACK
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
