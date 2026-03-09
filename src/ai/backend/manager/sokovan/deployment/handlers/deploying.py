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
from datetime import UTC, datetime
from typing import override

from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.common.data.notification.messages import EndpointLifecycleChangedMessage
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
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
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.evaluator import DeploymentStrategyEvaluator
from ai.backend.manager.sokovan.deployment.strategy.types import StrategyEvaluationSummary
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------


def build_lifecycle_notification_event(
    deployment: DeploymentInfo,
    from_status: EndpointLifecycle | None,
    to_status: EndpointLifecycle,
    transition_result: str,
    timestamp: str,
) -> NotificationTriggeredEvent:
    """Build a notification event for a lifecycle transition."""
    message = EndpointLifecycleChangedMessage(
        endpoint_id=str(deployment.id),
        endpoint_name=deployment.metadata.name,
        domain=deployment.metadata.domain,
        project_id=str(deployment.metadata.project),
        resource_group=deployment.metadata.resource_group,
        from_status=from_status.value if from_status else None,
        to_status=to_status.value,
        transition_result=transition_result,
        event_timestamp=timestamp,
    )
    return NotificationTriggeredEvent(
        rule_type=NotificationRuleType.ENDPOINT_LIFECYCLE_CHANGED.value,
        timestamp=datetime.now(UTC),
        notification_data=message.model_dump(),
    )


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
        """Run evaluation and apply side-effects (sub_step update + route changes)."""
        deployments = await self._deployment_repo.get_endpoints_by_statuses([
            EndpointLifecycle.DEPLOYING
        ])
        if not deployments:
            return
        log.info("pre-step evaluate: processing {} deployments", len(deployments))
        eval_result = await self._evaluator.evaluate(deployments)
        await self._update_sub_steps(eval_result)
        await self._apply_route_changes(eval_result)

    async def _update_sub_steps(self, eval_result: StrategyEvaluationSummary) -> None:
        """Bulk-update the sub_step column based on evaluation results."""
        if eval_result.assignments:
            await self._deployment_repo.update_sub_steps(eval_result.assignments)

    async def _apply_route_changes(self, eval_result: StrategyEvaluationSummary) -> None:
        """Apply aggregated route mutations from the evaluation result."""
        changes = eval_result.route_changes
        if not changes.rollout_specs and not changes.drain_route_ids:
            return

        scale_in_updater: BatchUpdater[RoutingRow] | None = None
        if changes.drain_route_ids:
            scale_in_updater = BatchUpdater(
                spec=RouteBatchUpdaterSpec(
                    status=RouteStatus.TERMINATING,
                    traffic_ratio=0.0,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                ),
                conditions=[RouteConditions.by_ids(changes.drain_route_ids)],
            )

        await self._deployment_repo.scale_routes(changes.rollout_specs, scale_in_updater)
        log.debug(
            "Applied route changes: {} created, {} terminated",
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
            match deployment.sub_step:
                case DeploymentSubStep.COMPLETED:
                    completed.append(deployment)
                case DeploymentSubStep.ROLLED_BACK:
                    rolled_back.append(deployment)
                case _:
                    pass  # PROGRESSING: still in progress — not included in result

        if completed:
            endpoint_ids = {deployment.id for deployment in completed}
            await self._deployment_repo.complete_deployment_revision_swap(endpoint_ids)
            log.info("Swapped revision for {} completed deployments", len(endpoint_ids))

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
