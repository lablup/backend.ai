"""Handlers for DEPLOYING sub-steps (BEP-1049).

Each handler is registered statically and targets deployments filtered by
their ``sub_step`` column in the DB.  The coordinator runs them in order:

1. **EvaluateHandler** — runs the strategy evaluator on all DEPLOYING
   deployments (regardless of sub_step), updates the ``sub_step`` column,
   and applies route mutations.
2. **ProvisioningHandler** — targets sub_step=PROVISIONING.
3. **ProgressingHandler** — targets sub_step=PROGRESSING.
4. **CompletedHandler** — targets sub_step=COMPLETED; revision swap → READY.
5. **RolledBackHandler** — targets sub_step=ROLLED_BACK; cleanup → READY.
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
from ai.backend.manager.sokovan.deployment.strategy.types import EvaluationResult
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# Evaluate handler (runs first, no sub_step filter)
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


class DeployingEvaluateHandler(DeploymentHandler):
    """Evaluates strategy for all DEPLOYING deployments.

    - Updates the ``sub_step`` column in DB (including COMPLETED/ROLLED_BACK).
    - Applies route mutations.
    """

    def __init__(
        self,
        evaluator: DeploymentStrategyEvaluator,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._evaluator = evaluator
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-evaluate"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        # No lifecycle transition via the standard coordinator path.
        # Completed/rolled-back transitions are handled directly.
        return DeploymentStatusTransitions(success=None, failure=None)

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        eval_result = await self._evaluator.evaluate(deployments)
        await self._update_sub_steps(eval_result)
        await self._apply_route_changes(eval_result)
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        pass

    # -- Private helpers --

    async def _update_sub_steps(self, eval_result: EvaluationResult) -> None:
        """Bulk-update the sub_step column based on evaluation results."""
        if eval_result.assignments:
            await self._deployment_repo.update_sub_steps(eval_result.assignments)

    async def _apply_route_changes(self, eval_result: EvaluationResult) -> None:
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
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        # Stay in DEPLOYING — no transition.
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
    def target_sub_step(cls) -> DeploymentSubStep | None:
        return DeploymentSubStep.PROVISIONING

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
    def target_sub_step(cls) -> DeploymentSubStep | None:
        return DeploymentSubStep.PROGRESSING

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
# Terminal handlers (COMPLETED / ROLLED_BACK)
# ---------------------------------------------------------------------------


class DeployingCompletedHandler(DeploymentHandler):
    """Handler for DEPLOYING / COMPLETED sub-step.

    Performs revision swap only.  Lifecycle transition to READY is handled
    by the coordinator via ``status_transitions()``.
    """

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-completed"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return None

    @classmethod
    @override
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def target_sub_step(cls) -> DeploymentSubStep | None:
        return DeploymentSubStep.COMPLETED

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_status=DeploymentSubStep.COMPLETED,
            ),
            failure=None,
        )

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        endpoint_ids = {d.id for d in deployments}
        await self._deployment_repo.complete_deployment_revision_swap(endpoint_ids)
        log.info("Swapped revision for {} completed deployments", len(endpoint_ids))
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        pass


class DeployingRolledBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLED_BACK sub-step.

    Clears deploying_revision only.  Lifecycle transition to READY is handled
    by the coordinator via ``status_transitions()``.
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
        return None

    @classmethod
    @override
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    @override
    def target_sub_step(cls) -> DeploymentSubStep | None:
        return DeploymentSubStep.ROLLED_BACK

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
