"""
Deployment coordinator for managing deployment lifecycle.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.common.data.notification.messages import EndpointLifecycleChangedMessage
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.common.events.event_types.schedule.anycast import (
    DoDeploymentLifecycleEvent,
    DoDeploymentLifecycleIfNeededEvent,
)
from ai.backend.common.leader.tasks.event_task import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentSubStatus,
    DeploymentSubStep,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import (
    DeploymentConditions,
    DeploymentRepository,
)
from ai.backend.manager.repositories.deployment.creators import (
    EndpointLifecycleBatchUpdaterSpec,
    RouteBatchUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.scheduling_history.creators import DeploymentHistoryCreatorSpec
from ai.backend.manager.sokovan.deployment.recorder import DeploymentRecorderContext
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from ai.backend.manager.types import DistributedLockFactory

from .deployment_controller import DeploymentController
from .executor import DeploymentExecutor
from .handlers import (
    CheckPendingDeploymentHandler,
    CheckReplicaDeploymentHandler,
    DeployingProgressingHandler,
    DeployingProvisioningHandler,
    DeployingRolledBackHandler,
    DeploymentHandler,
    DestroyingDeploymentHandler,
    ReconcileDeploymentHandler,
    ScalingDeploymentHandler,
)
from .strategy.evaluator import DeploymentStrategyEvaluator
from .strategy.types import EvaluationResult
from .types import DeploymentExecutionResult, DeploymentLifecycleType

# Handler key: either a simple lifecycle type or a (lifecycle, sub-step) tuple
type DeploymentHandlerKey = (
    DeploymentLifecycleType | tuple[DeploymentLifecycleType, DeploymentSubStep]
)

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class DeploymentTaskSpec:
    """Specification for a deployment lifecycle periodic task."""

    lifecycle_type: DeploymentLifecycleType
    short_interval: float | None = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoDeploymentLifecycleIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoDeploymentLifecycleIfNeededEvent(self.lifecycle_type.value)

    def create_process_event(self) -> DoDeploymentLifecycleEvent:
        """Create event for forced processing."""
        return DoDeploymentLifecycleEvent(self.lifecycle_type.value)

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"deployment_process_if_needed_{self.lifecycle_type.value}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
        return f"deployment_process_{self.lifecycle_type.value}"


class DeploymentCoordinator:
    """Coordinates deployment-related operations."""

    _valkey_schedule: ValkeyScheduleClient
    _deployment_controller: DeploymentController
    _deployment_repository: DeploymentRepository
    _deployment_handlers: Mapping[DeploymentHandlerKey, DeploymentHandler]
    _deployment_evaluators: Mapping[DeploymentLifecycleType, DeploymentStrategyEvaluator]
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        deployment_controller: DeploymentController,
        deployment_repository: DeploymentRepository,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
        scheduling_controller: SchedulingController,
        client_pool: ClientPool,
        valkey_stat: ValkeyStatClient,
        route_controller: RouteController,
    ) -> None:
        """Initialize the deployment coordinator."""
        self._valkey_schedule = valkey_schedule
        self._deployment_controller = deployment_controller
        self._deployment_repository = deployment_repository
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = config_provider
        self._route_controller = route_controller

        # Create deployment executor
        executor = DeploymentExecutor(
            deployment_repo=self._deployment_repository,
            scheduling_controller=scheduling_controller,
            config_provider=self._config_provider,
            client_pool=client_pool,
            valkey_stat=valkey_stat,
        )
        self._deployment_handlers = self._init_handlers(executor)
        self._deployment_evaluators = {
            DeploymentLifecycleType.DEPLOYING: DeploymentStrategyEvaluator(
                deployment_repo=self._deployment_repository,
            ),
        }

    def _init_handlers(
        self, executor: DeploymentExecutor
    ) -> Mapping[DeploymentHandlerKey, DeploymentHandler]:
        """Initialize and return the mapping of handler keys to their handlers."""
        handlers: dict[DeploymentHandlerKey, DeploymentHandler] = {
            DeploymentLifecycleType.CHECK_PENDING: CheckPendingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.CHECK_REPLICA: CheckReplicaDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.SCALING: ScalingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
                route_controller=self._route_controller,
            ),
            DeploymentLifecycleType.RECONCILE: ReconcileDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.DESTROYING: DestroyingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
                route_controller=self._route_controller,
            ),
            # DEPLOYING sub-step handlers (keyed by composite key)
            (DeploymentLifecycleType.DEPLOYING, DeploymentSubStep.PROVISIONING): (
                DeployingProvisioningHandler(
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                )
            ),
            (DeploymentLifecycleType.DEPLOYING, DeploymentSubStep.PROGRESSING): (
                DeployingProgressingHandler(
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                )
            ),
            (DeploymentLifecycleType.DEPLOYING, DeploymentSubStep.ROLLED_BACK): (
                DeployingRolledBackHandler(
                    deployment_repo=self._deployment_repository,
                )
            ),
        }
        return handlers

    async def process_deployment_lifecycle(
        self,
        lifecycle_type: DeploymentLifecycleType,
    ) -> None:
        # Check if this lifecycle type uses an evaluator (e.g. DEPLOYING)
        evaluator = self._deployment_evaluators.get(lifecycle_type)
        if evaluator is not None:
            await self._process_with_evaluator(lifecycle_type, evaluator)
            return

        handler = self._deployment_handlers.get(lifecycle_type)
        if not handler:
            log.warning("No handler for deployment lifecycle type: {}", lifecycle_type.value)
            return
        async with AsyncExitStack() as stack:
            if handler.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(handler.lock_id, lock_lifetime))
            deployments = await self._deployment_repository.get_endpoints_by_statuses(
                handler.target_statuses()
            )
            if not deployments:
                log.trace("No deployments to process for handler: {}", handler.name())
                return
            log.info("handler: {} - processing {} deployments", handler.name(), len(deployments))

            # Execute handler with recorder context
            deployment_ids = [d.id for d in deployments]
            with DeploymentRecorderContext.scope(
                lifecycle_type.value, entity_ids=deployment_ids
            ) as pool:
                result = await handler.execute(deployments)
                all_records = pool.build_all_records()

                # Handle status transitions with history recording
                await self._handle_status_transitions(handler, result, all_records)

            try:
                await handler.post_process(result)
            except Exception as e:
                log.error("Error during post-processing: {}", e)

    async def _handle_status_transitions(
        self,
        handler: DeploymentHandler,
        result: DeploymentExecutionResult,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Handle status transitions with history recording.

        All transitions (success and failure) are processed in a single transaction
        to ensure atomicity.

        Args:
            handler: The deployment handler that was executed
            result: The result of the handler execution
            records: Execution records from the recorder context
        """
        handler_name = handler.name()
        target_statuses = handler.target_statuses()
        from_status = target_statuses[0] if target_statuses else None

        # Collect all batch updaters and history specs
        batch_updaters: list[BatchUpdater[EndpointRow]] = []
        all_history_specs: list[DeploymentHistoryCreatorSpec] = []
        notification_events: list[NotificationTriggeredEvent] = []
        timestamp_now = datetime.now(UTC).isoformat()

        # Handle success transitions
        transitions = handler.status_transitions()
        next_lifecycle_status = transitions.success
        if next_lifecycle_status is not None and result.successes:
            next_lifecycle = next_lifecycle_status.lifecycle
            sub_status = next_lifecycle_status.sub_status
            endpoint_ids = [d.id for d in result.successes]
            success_history_specs = [
                DeploymentHistoryCreatorSpec(
                    deployment_id=d.id,
                    phase=handler_name,
                    result=SchedulingResult.SUCCESS,
                    message=f"{handler_name} completed successfully",
                    from_status=from_status,
                    to_status=next_lifecycle,
                    sub_steps=self._build_history_sub_steps(
                        d.id, records, sub_status, SchedulingResult.SUCCESS
                    ),
                )
                for d in result.successes
            ]
            batch_updaters.append(
                BatchUpdater(
                    spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=next_lifecycle),
                    conditions=[
                        DeploymentConditions.by_ids(endpoint_ids),
                        DeploymentConditions.by_lifecycle_stages(target_statuses),
                    ],
                )
            )
            all_history_specs.extend(success_history_specs)
            notification_events.extend([
                self._build_lifecycle_notification_event(
                    deployment=d,
                    from_status=from_status,
                    to_status=next_lifecycle,
                    transition_result="success",
                    timestamp=timestamp_now,
                )
                for d in result.successes
            ])

        # Handle failure transitions
        failure_lifecycle_status = transitions.failure
        if failure_lifecycle_status is not None and result.errors:
            failure_lifecycle = failure_lifecycle_status.lifecycle
            failure_sub_status = failure_lifecycle_status.sub_status
            endpoint_ids = [e.deployment_info.id for e in result.errors]
            failure_history_specs = [
                DeploymentHistoryCreatorSpec(
                    deployment_id=e.deployment_info.id,
                    phase=handler_name,
                    result=SchedulingResult.FAILURE,
                    message=e.reason,
                    from_status=from_status,
                    to_status=failure_lifecycle,
                    error_code=e.error_code,
                    sub_steps=self._build_history_sub_steps(
                        e.deployment_info.id, records, failure_sub_status, SchedulingResult.FAILURE
                    ),
                )
                for e in result.errors
            ]
            batch_updaters.append(
                BatchUpdater(
                    spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=failure_lifecycle),
                    conditions=[
                        DeploymentConditions.by_ids(endpoint_ids),
                        DeploymentConditions.by_lifecycle_stages(target_statuses),
                    ],
                )
            )
            all_history_specs.extend(failure_history_specs)
            notification_events.extend([
                self._build_lifecycle_notification_event(
                    deployment=e.deployment_info,
                    from_status=from_status,
                    to_status=failure_lifecycle,
                    transition_result="failure",
                    timestamp=timestamp_now,
                )
                for e in result.errors
            ])

        # Execute all updates in a single transaction
        if batch_updaters:
            await self._deployment_repository.update_endpoint_lifecycle_bulk_with_history(
                batch_updaters, BulkCreator(specs=all_history_specs)
            )

        # Anycast notification events
        for event in notification_events:
            try:
                await self._event_producer.anycast_event(event)
            except Exception as e:
                log.warning("Failed to send lifecycle notification: {}", e)

    async def _process_with_evaluator(
        self,
        lifecycle_type: DeploymentLifecycleType,
        evaluator: DeploymentStrategyEvaluator,
    ) -> None:
        """Process deployments that use a strategy evaluator (e.g. DEPLOYING).

        1. Acquire distributed lock.
        2. Load DEPLOYING deployments.
        3. Run evaluator (evaluates strategy FSM, aggregates route mutations).
        4. Apply aggregated route mutations.
        5. For each sub-step group, run the corresponding handler.
        6. Handle errors and skipped deployments.
        7. For completed deployments, swap revisions and transition to READY.
        """
        lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
        async with self._lock_factory(LockID.LOCKID_DEPLOYMENT_DEPLOYING, lock_lifetime):
            deployments = await self._deployment_repository.get_endpoints_by_statuses([
                EndpointLifecycle.DEPLOYING
            ])
            if not deployments:
                log.trace("No DEPLOYING deployments to process")
                return
            log.info("DEPLOYING: processing {} deployments", len(deployments))

            deployment_ids = [d.id for d in deployments]
            sub_results: dict[DeploymentSubStep, DeploymentExecutionResult] = {}
            with DeploymentRecorderContext.scope(
                lifecycle_type.value, entity_ids=deployment_ids
            ) as pool:
                eval_result = await evaluator.evaluate(deployments)

                # Apply aggregated route mutations from the evaluation
                await self._apply_route_changes(eval_result)

                all_records = pool.build_all_records()

                # Process each sub-step group with its handler
                for sub_step, group in eval_result.groups.items():
                    handler_key: DeploymentHandlerKey = (lifecycle_type, sub_step)
                    handler = self._deployment_handlers.get(handler_key)
                    if handler is None:
                        log.warning(
                            "No handler for sub-step {}/{}", lifecycle_type.value, sub_step.value
                        )
                        continue

                    sub_result = await handler.execute(group.deployments)
                    sub_results[sub_step] = sub_result
                    await self._handle_status_transitions(handler, sub_result, all_records)

            # Handle evaluation errors (Finding 3) — record history, keep DEPLOYING
            if eval_result.errors:
                error_history_specs = [
                    DeploymentHistoryCreatorSpec(
                        deployment_id=deployment.id,
                        phase=lifecycle_type.value,
                        result=SchedulingResult.NEED_RETRY,
                        message=f"Evaluation error: {reason}",
                        from_status=EndpointLifecycle.DEPLOYING,
                        to_status=None,
                        sub_steps=[],
                    )
                    for deployment, reason in eval_result.errors
                ]
                await self._deployment_repository.update_endpoint_lifecycle_bulk_with_history(
                    [], BulkCreator(specs=error_history_specs)
                )
                for deployment, reason in eval_result.errors:
                    log.error("Deployment {} evaluation error: {}", deployment.id, reason)

            # Handle skipped deployments (Finding 5) — record history, keep DEPLOYING
            if eval_result.skipped:
                skipped_history_specs = [
                    DeploymentHistoryCreatorSpec(
                        deployment_id=deployment.id,
                        phase=lifecycle_type.value,
                        result=SchedulingResult.SKIPPED,
                        message="No deployment policy found",
                        from_status=EndpointLifecycle.DEPLOYING,
                        to_status=None,
                        sub_steps=[],
                    )
                    for deployment in eval_result.skipped
                ]
                await self._deployment_repository.update_endpoint_lifecycle_bulk_with_history(
                    [], BulkCreator(specs=skipped_history_specs)
                )
                for deployment in eval_result.skipped:
                    log.warning("Deployment {} skipped: no deployment policy found", deployment.id)

            # Post-process outside recorder scope using actual sub_results (Finding 4)
            for sub_step, group in eval_result.groups.items():
                handler_key = (lifecycle_type, sub_step)
                handler = self._deployment_handlers.get(handler_key)
                if handler is None:
                    continue
                try:
                    actual_result = sub_results.get(
                        sub_step,
                        DeploymentExecutionResult(successes=group.deployments),
                    )
                    await handler.post_process(actual_result)
                except Exception as e:
                    log.error(
                        "Error during post-processing for sub-step {}: {}",
                        sub_step.value,
                        e,
                    )

            # Transition completed deployments: swap revision and move to READY
            if eval_result.completed:
                await self._transition_completed_deployments(
                    lifecycle_type,
                    eval_result.completed,
                    strategies=eval_result.completed_strategies,
                    records=all_records,
                )

    async def _apply_route_changes(
        self,
        eval_result: EvaluationResult,
    ) -> None:
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

        await self._deployment_repository.scale_routes(changes.rollout_specs, scale_in_updater)
        log.debug(
            "Applied route changes: {} created, {} terminated",
            len(changes.rollout_specs),
            len(changes.drain_route_ids),
        )

    async def _transition_completed_deployments(
        self,
        lifecycle_type: DeploymentLifecycleType,
        completed: list[DeploymentInfo],
        strategies: dict[UUID, DeploymentStrategy],
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Transition completed DEPLOYING deployments to READY.

        Atomically:
        1. Swap deploying_revision → current_revision (with idempotency guard).
        2. Update lifecycle to READY with history recording.
        3. Send notification events.
        """
        endpoint_ids = {deployment.id for deployment in completed}

        # Build lifecycle transition
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
                phase=lifecycle_type.value,
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
        await self._deployment_repository.complete_deployment_and_transition_to_ready(
            endpoint_ids, [batch_updater], BulkCreator(specs=history_specs)
        )
        log.info(
            "Atomically swapped revision and transitioned {} deployments to READY",
            len(endpoint_ids),
        )

        # Send notifications
        for deployment in completed:
            try:
                event = self._build_lifecycle_notification_event(
                    deployment=deployment,
                    from_status=from_status,
                    to_status=to_status,
                    transition_result="success",
                    timestamp=timestamp_now,
                )
                await self._event_producer.anycast_event(event)
            except Exception as e:
                log.warning("Failed to send lifecycle notification: {}", e)

    @staticmethod
    def _build_history_sub_steps(
        entity_id: UUID,
        records: Mapping[UUID, ExecutionRecord],
        sub_status: DeploymentSubStatus | None,
        scheduling_result: SchedulingResult,
    ) -> list[SubStepResult]:
        """Build sub_steps list, appending sub_status as an entry if present."""
        sub_steps = extract_sub_steps_for_entity(entity_id, records)
        if sub_status is not None:
            now = datetime.now(UTC)
            sub_steps.append(
                SubStepResult(
                    step=sub_status.value,
                    result=scheduling_result,
                    started_at=now,
                    ended_at=now,
                )
            )
        return sub_steps

    def _build_lifecycle_notification_event(
        self,
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

    async def process_if_needed(self, lifecycle_type: DeploymentLifecycleType) -> None:
        """
        Process deployment lifecycle operation if needed (based on internal state).

        Args:
            lifecycle_type: Type of deployment lifecycle operation

        Returns:
            True if operation was performed, False otherwise
        """
        # Check internal state (uses Redis marks)
        if not await self._valkey_schedule.load_and_delete_deployment_mark(lifecycle_type.value):
            return
        await self.process_deployment_lifecycle(lifecycle_type)

    @staticmethod
    def _create_task_specs() -> list[DeploymentTaskSpec]:
        """Create task specifications for all deployment lifecycle types."""
        return [
            # Check pending deployments frequently with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.CHECK_PENDING,
                short_interval=2.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Check replicas moderately with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.CHECK_REPLICA,
                short_interval=5.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Scaling operations with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.SCALING,
                short_interval=5.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            DeploymentTaskSpec(
                DeploymentLifecycleType.RECONCILE,
                short_interval=None,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Deploying (rolling update) - both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.DEPLOYING,
                short_interval=5.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Check destroying deployments - only long cycle
            DeploymentTaskSpec(
                DeploymentLifecycleType.DESTROYING,
                short_interval=5.0,
                long_interval=60.0,
                initial_delay=25.0,
            ),
        ]

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for deployment lifecycle events."""
        task_specs = self._create_task_specs()
        specs: list[EventTaskSpec] = []

        for spec in task_specs:
            # Create short-cycle task spec if specified
            if spec.short_interval is not None:
                short_spec = EventTaskSpec(
                    name=spec.short_task_name,
                    event_factory=spec.create_if_needed_event,
                    interval=spec.short_interval,
                    initial_delay=0.0,  # Start immediately for short tasks
                )
                specs.append(short_spec)

            # Create long-cycle task spec (always present)
            long_spec = EventTaskSpec(
                name=spec.long_task_name,
                event_factory=spec.create_process_event,
                interval=spec.long_interval,
                initial_delay=spec.initial_delay,
            )
            specs.append(long_spec)

        return specs
