"""Handlers for DEPLOYING sub-steps (BEP-1049).

In-progress handlers (PROVISIONING, PROGRESSING) run *after* the coordinator
has applied route mutations from the evaluation result.  Their ``execute``
simply returns success.  ``post_process`` triggers the next DEPLOYING cycle
and route provisioning.

The rolled-back handler clears ``deploying_revision`` and transitions the
deployment back to READY.

The composite ``DeployingHandler`` encapsulates strategy evaluation, route
mutations, sub-step dispatch, and completed deployment transitions so that
the coordinator can treat DEPLOYING identically to every other lifecycle type.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.common.data.notification.messages import EndpointLifecycleChangedMessage
from ai.backend.common.events.dispatcher import EventProducer
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
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import DeploymentConditions
from ai.backend.manager.repositories.deployment.creators import (
    EndpointLifecycleBatchUpdaterSpec,
    RouteBatchUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduling_history.creators import DeploymentHistoryCreatorSpec
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.evaluator import DeploymentStrategyEvaluator
from ai.backend.manager.sokovan.deployment.strategy.types import EvaluationGroup, EvaluationResult
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity

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


# ---------------------------------------------------------------------------
# Composite handler
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


class DeployingHandler(DeploymentHandler):
    """Composite handler for DEPLOYING lifecycle.

    Encapsulates strategy evaluation, route mutations, sub-step dispatch,
    and completed deployment transitions so the coordinator treats DEPLOYING
    identically to every other lifecycle type.
    """

    def __init__(
        self,
        evaluator: DeploymentStrategyEvaluator,
        sub_step_handlers: Mapping[DeploymentSubStep, DeploymentHandler],
        deployment_repo: DeploymentRepository,
        event_producer: EventProducer,
    ) -> None:
        self._evaluator = evaluator
        self._sub_step_handlers = sub_step_handlers
        self._deployment_repo = deployment_repo
        self._event_producer = event_producer
        self._eval_result: EvaluationResult | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying"

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
        return DeploymentStatusTransitions(success=None, failure=None)

    @override
    async def prepare(
        self, deployments: Sequence[DeploymentInfo]
    ) -> list[tuple[DeploymentHandler, Sequence[DeploymentInfo]]]:
        """Run evaluator, apply route changes, return sub-step handler tasks."""
        eval_result = await self._evaluator.evaluate(deployments)
        self._eval_result = eval_result
        await self._apply_route_changes(eval_result)
        return self._resolve_handler_tasks(eval_result.groups)

    @override
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        # Not called directly; prepare() returns sub-step handlers
        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        # Not called directly; sub-step handlers handle post-processing
        pass

    @override
    async def finalize(self, records: Mapping[UUID, ExecutionRecord]) -> None:
        """Record evaluation outcomes and transition completed deployments."""
        eval_result = self._eval_result
        if eval_result is None:
            return
        await self._record_evaluation_outcomes(eval_result)
        if eval_result.completed:
            await self._transition_completed_deployments(eval_result, records)
        self._eval_result = None

    # -- Private helpers (moved from coordinator) --

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

    def _resolve_handler_tasks(
        self, groups: dict[DeploymentSubStep, EvaluationGroup]
    ) -> list[tuple[DeploymentHandler, Sequence[DeploymentInfo]]]:
        """Resolve sub-step groups into handler-deployment pairs."""
        tasks: list[tuple[DeploymentHandler, Sequence[DeploymentInfo]]] = []
        for sub_step, group in groups.items():
            handler = self._sub_step_handlers.get(sub_step)
            if handler is None:
                log.warning("No handler for DEPLOYING sub-step {}", sub_step.value)
                continue
            tasks.append((handler, group.deployments))
        return tasks

    async def _record_evaluation_outcomes(self, eval_result: EvaluationResult) -> None:
        """Record history for evaluation errors and skipped deployments."""
        lifecycle_value = DeploymentLifecycleType.DEPLOYING.value

        if eval_result.errors:
            error_history_specs = [
                DeploymentHistoryCreatorSpec(
                    deployment_id=deployment.id,
                    phase=lifecycle_value,
                    result=SchedulingResult.NEED_RETRY,
                    message=f"Evaluation error: {reason}",
                    from_status=EndpointLifecycle.DEPLOYING,
                    to_status=None,
                    sub_steps=[],
                )
                for deployment, reason in eval_result.errors
            ]
            await self._deployment_repo.update_endpoint_lifecycle_bulk_with_history(
                [], BulkCreator(specs=error_history_specs)
            )
            for deployment, reason in eval_result.errors:
                log.error("Deployment {} evaluation error: {}", deployment.id, reason)

        if eval_result.skipped:
            skipped_history_specs = [
                DeploymentHistoryCreatorSpec(
                    deployment_id=deployment.id,
                    phase=lifecycle_value,
                    result=SchedulingResult.SKIPPED,
                    message="No deployment policy found",
                    from_status=EndpointLifecycle.DEPLOYING,
                    to_status=None,
                    sub_steps=[],
                )
                for deployment in eval_result.skipped
            ]
            await self._deployment_repo.update_endpoint_lifecycle_bulk_with_history(
                [], BulkCreator(specs=skipped_history_specs)
            )
            for deployment in eval_result.skipped:
                log.warning("Deployment {} skipped: no deployment policy found", deployment.id)

    async def _transition_completed_deployments(
        self,
        eval_result: EvaluationResult,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Transition completed DEPLOYING deployments to READY.

        Atomically:
        1. Swap deploying_revision -> current_revision (with idempotency guard).
        2. Update lifecycle to READY with history recording.
        3. Send notification events.
        """
        completed = eval_result.completed
        strategies = eval_result.completed_strategies
        endpoint_ids = {deployment.id for deployment in completed}
        lifecycle_value = DeploymentLifecycleType.DEPLOYING.value

        target_statuses = [EndpointLifecycle.DEPLOYING]
        from_status = EndpointLifecycle.DEPLOYING
        to_status = EndpointLifecycle.READY

        batch_updater = BatchUpdater(
            spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=to_status),
            conditions=[
                DeploymentConditions.by_ids(list(endpoint_ids)),
                DeploymentConditions.by_lifecycle_stages(target_statuses),
            ],
        )

        timestamp_now = datetime.now(UTC).isoformat()
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=deployment.id,
                phase=lifecycle_value,
                result=SchedulingResult.SUCCESS,
                message=f"Deployment completed successfully (strategy: {strategies[deployment.id].value})"
                if deployment.id in strategies
                else "Deployment completed successfully",
                from_status=from_status,
                to_status=to_status,
                sub_steps=extract_sub_steps_for_entity(deployment.id, records),
            )
            for deployment in completed
        ]

        # Atomic: revision swap + lifecycle update + history recording
        await self._deployment_repo.complete_deployment_and_transition_to_ready(
            endpoint_ids, [batch_updater], BulkCreator(specs=history_specs)
        )
        log.info(
            "Atomically swapped revision and transitioned {} deployments to READY",
            len(endpoint_ids),
        )

        # Send notifications
        for deployment in completed:
            try:
                event = build_lifecycle_notification_event(
                    deployment=deployment,
                    from_status=from_status,
                    to_status=to_status,
                    transition_result="success",
                    timestamp=timestamp_now,
                )
                await self._event_producer.anycast_event(event)
            except Exception as e:
                log.warning("Failed to send lifecycle notification: {}", e)
