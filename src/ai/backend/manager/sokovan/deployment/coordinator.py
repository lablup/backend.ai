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
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentLifecycleStatus
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.defs import SERVICE_MAX_RETRIES
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import (
    DeploymentConditions,
    DeploymentRepository,
)
from ai.backend.manager.repositories.deployment.creators import EndpointLifecycleBatchUpdaterSpec
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
    DeploymentHandler,
    DestroyingDeploymentHandler,
    ReconcileDeploymentHandler,
    ScalingDeploymentHandler,
)
from .types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

# Timeout thresholds for deployment lifecycle statuses (seconds).
DEPLOYMENT_STATUS_TIMEOUT_MAP: dict[EndpointLifecycle, float] = {
    EndpointLifecycle.DEPLOYING: 1800.0,  # 30 minutes
    EndpointLifecycle.SCALING: 1800.0,  # 30 minutes
}


def _is_transition_timed_out(
    started_at: datetime | None,
    lifecycle: EndpointLifecycle,
    current_dbtime: datetime,
) -> bool:
    """Check if timeout exceeded for the given lifecycle status."""
    if started_at is None:
        return False
    timeout = DEPLOYMENT_STATUS_TIMEOUT_MAP.get(lifecycle)
    if not timeout:
        return False
    # Normalise both to UTC to avoid timezone-naive vs -aware
    # comparison errors (DB may return either depending on driver).
    current_utc = (
        current_dbtime.astimezone(UTC)
        if current_dbtime.tzinfo
        else current_dbtime.replace(tzinfo=UTC)
    )
    started_utc = (
        started_at.astimezone(UTC) if started_at.tzinfo else started_at.replace(tzinfo=UTC)
    )
    elapsed = (current_utc - started_utc).total_seconds()
    return elapsed > timeout


@dataclass
class FailureClassificationResult:
    """Result of classifying failures into give_up, expired, and need_retry.

    Classification priority (first match wins):
    1. give_up: phase_attempts >= SERVICE_MAX_RETRIES
    2. expired: phase_started_at elapsed > DEPLOYMENT_STATUS_TIMEOUT_MAP threshold
    3. need_retry: default (can be retried)
    """

    give_up: list[DeploymentExecutionError]
    """Deployments that exceeded max retries — should transition to give_up status."""

    expired: list[DeploymentExecutionError]
    """Deployments that exceeded timeout threshold — should transition to expired status."""

    need_retry: list[DeploymentExecutionError]
    """Deployments that can be retried — should transition to need_retry status."""


@dataclass
class _TransitionResult:
    """Result of building a lifecycle transition."""

    updater: BatchUpdater[EndpointRow]
    history_specs: list[DeploymentHistoryCreatorSpec]
    notification_events: list[NotificationTriggeredEvent]


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
    _deployment_handlers: Mapping[DeploymentLifecycleType, DeploymentHandler]
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

    def _init_handlers(
        self, executor: DeploymentExecutor
    ) -> Mapping[DeploymentLifecycleType, DeploymentHandler]:
        """Initialize and return the mapping of deployment lifecycle types to their handlers."""
        return {
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
        }

    async def process_deployment_lifecycle(
        self,
        lifecycle_type: DeploymentLifecycleType,
    ) -> None:
        handler = self._deployment_handlers.get(lifecycle_type)
        if not handler:
            log.warning("No handler for deployment lifecycle type: {}", lifecycle_type.value)
            return
        async with AsyncExitStack() as stack:
            if handler.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(handler.lock_id, lock_lifetime))
            handler_name = handler.name()
            target_statuses = handler.target_statuses()
            lifecycle_stages = [s.lifecycle for s in target_statuses]
            deployments = await self._deployment_repository.get_deployments_for_handler(
                lifecycle_stages, handler_name
            )
            if not deployments:
                log.trace("No deployments to process for handler: {}", handler_name)
                return
            log.info("handler: {} - processing {} deployments", handler_name, len(deployments))

            deployment_ids = [deployment.deployment_info.id for deployment in deployments]

            with DeploymentRecorderContext.scope(handler_name, entity_ids=deployment_ids) as pool:
                try:
                    result = await handler.execute(deployments)
                except Exception:
                    log.exception("handler {}: execute() raised an unexpected error", handler_name)
                    result = DeploymentExecutionResult(
                        errors=[
                            DeploymentExecutionError(
                                deployment_info=deployment,
                                reason=f"Unexpected error in {handler_name}",
                                error_detail="handler execute() raised an unhandled exception",
                            )
                            for deployment in deployments
                        ],
                    )
                all_records = pool.build_all_records()
                await self._handle_status_transitions(handler, result, all_records)

            try:
                await handler.post_process(result)
            except Exception as e:
                log.error("Error during post-processing for {}: {}", handler.name(), e)

    async def _handle_status_transitions(
        self,
        handler: DeploymentHandler,
        result: DeploymentExecutionResult,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Handle status transitions with history recording.

        Classifies failures into need_retry/expired/give_up using phase_attempts
        and phase_started_at from DeploymentWithHistory embedded in each error,
        then applies per-category transitions. All transitions are processed
        in a single transaction.
        """
        handler_name = handler.name()
        target_statuses = handler.target_statuses()
        from_status = target_statuses[0].lifecycle if target_statuses else None
        target_lifecycle_stages = [s.lifecycle for s in target_statuses]

        batch_updaters: list[BatchUpdater[EndpointRow]] = []
        all_history_specs: list[DeploymentHistoryCreatorSpec] = []
        notification_events: list[NotificationTriggeredEvent] = []
        timestamp_now = datetime.now(UTC).isoformat()

        transitions = handler.status_transitions()

        # Success transitions (None = stay in current state)
        if transitions.success is not None and result.successes:
            transition = self._build_success_transition(
                handler_name=handler_name,
                deployments=result.successes,
                lifecycle_status=transitions.success,
                target_lifecycles=target_statuses,
                records=records,
                timestamp_now=timestamp_now,
            )
            batch_updaters.append(transition.updater)
            all_history_specs.extend(transition.history_specs)
            notification_events.extend(transition.notification_events)

        # Failure transitions — classify into need_retry/expired/give_up
        if result.errors:
            current_dbtime = await self._deployment_repository.get_db_now()
            classified = self._classify_failures(result.errors, current_dbtime)

            failure_categories = [
                (classified.give_up, transitions.give_up, SchedulingResult.GIVE_UP, "give_up"),
                (classified.expired, transitions.expired, SchedulingResult.EXPIRED, "expired"),
                (
                    classified.need_retry,
                    transitions.need_retry,
                    SchedulingResult.NEED_RETRY,
                    "need_retry",
                ),
            ]
            for errors, lifecycle_status, scheduling_result, label in failure_categories:
                if not errors:
                    continue
                # No transition defined → stay in current state
                if not lifecycle_status:
                    continue
                transition = self._build_failure_transition(
                    handler_name=handler_name,
                    errors=errors,
                    lifecycle_status=lifecycle_status,
                    scheduling_result=scheduling_result,
                    target_lifecycles=target_statuses,
                    records=records,
                    timestamp_now=timestamp_now,
                    transition_label=label,
                )
                batch_updaters.append(transition.updater)
                all_history_specs.extend(transition.history_specs)
                notification_events.extend(transition.notification_events)

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

    def _build_lifecycle_updater(
        self,
        endpoint_ids: list[UUID],
        lifecycle_status: DeploymentLifecycleStatus,
        target_lifecycles: list[EndpointLifecycle],
    ) -> BatchUpdater[EndpointRow]:
        return BatchUpdater(
            spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=lifecycle_status.lifecycle),
            conditions=[
                DeploymentConditions.by_ids(endpoint_ids),
                DeploymentConditions.by_lifecycle_stages(target_lifecycles),
            ],
        )

    def _build_success_transition(
        self,
        *,
        handler_name: str,
        deployments: list[DeploymentWithHistory],
        lifecycle_status: DeploymentLifecycleStatus,
        target_lifecycles: list[DeploymentLifecycleStatus],
        records: Mapping[UUID, ExecutionRecord],
        timestamp_now: str,
    ) -> _TransitionResult:
        next_lifecycle = lifecycle_status.lifecycle
        from_status = target_lifecycles[0].lifecycle if target_lifecycles else None
        target_lifecycle_stages = [s.lifecycle for s in target_lifecycles]
        endpoint_ids = [deployment.deployment_info.id for deployment in deployments]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=deployment.deployment_info.id,
                phase=handler_name,
                result=SchedulingResult.SUCCESS,
                message=f"{handler_name} completed successfully",
                from_status=from_status,
                to_status=next_lifecycle,
                sub_steps=extract_sub_steps_for_entity(deployment.deployment_info.id, records),
            )
            for deployment in deployments
        ]
        events = [
            self._build_lifecycle_notification_event(
                deployment=deployment.deployment_info,
                from_status=from_status,
                to_status=next_lifecycle,
                transition_result="success",
                timestamp=timestamp_now,
            )
            for deployment in deployments
        ]
        updater = self._build_lifecycle_updater(
            endpoint_ids, lifecycle_status, target_lifecycle_stages
        )
        return _TransitionResult(
            updater=updater,
            history_specs=history_specs,
            notification_events=events,
        )

    def _build_failure_transition(
        self,
        *,
        handler_name: str,
        errors: list[DeploymentExecutionError],
        lifecycle_status: DeploymentLifecycleStatus,
        scheduling_result: SchedulingResult,
        target_lifecycles: list[DeploymentLifecycleStatus],
        records: Mapping[UUID, ExecutionRecord],
        timestamp_now: str,
        transition_label: str,
    ) -> _TransitionResult:
        next_lifecycle = lifecycle_status.lifecycle
        from_status = target_lifecycles[0].lifecycle if target_lifecycles else None
        target_lifecycle_stages = [s.lifecycle for s in target_lifecycles]
        endpoint_ids = [error.deployment_info.deployment_info.id for error in errors]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=error.deployment_info.deployment_info.id,
                phase=handler_name,
                result=scheduling_result,
                message=error.reason,
                from_status=from_status,
                to_status=next_lifecycle,
                error_code=error.error_code,
                sub_steps=extract_sub_steps_for_entity(
                    error.deployment_info.deployment_info.id, records
                ),
            )
            for error in errors
        ]
        events = [
            self._build_lifecycle_notification_event(
                deployment=error.deployment_info.deployment_info,
                from_status=from_status,
                to_status=next_lifecycle,
                transition_result=transition_label,
                timestamp=timestamp_now,
            )
            for error in errors
        ]
        updater = self._build_lifecycle_updater(
            endpoint_ids, lifecycle_status, target_lifecycle_stages
        )
        return _TransitionResult(
            updater=updater,
            history_specs=history_specs,
            notification_events=events,
        )

    @staticmethod
    def _classify_failures(
        errors: list[DeploymentExecutionError],
        current_dbtime: datetime,
    ) -> FailureClassificationResult:
        """Classify failures into give_up, expired, need_retry.

        Pure classification based on conditions only. The caller (_handle_status_transitions)
        decides whether to apply transitions based on handler's transition definitions.

        Classification priority (first match wins):
        1. give_up: phase_attempts >= SERVICE_MAX_RETRIES
        2. expired: timeout exceeded
        3. need_retry: default

        Args:
            errors: Failed deployment execution errors (each contains DeploymentWithHistory
                    with phase_attempts and phase_started_at populated)
            current_dbtime: Current database time for timeout comparison
        """
        give_up_errors: list[DeploymentExecutionError] = []
        expired_errors: list[DeploymentExecutionError] = []
        retry_errors: list[DeploymentExecutionError] = []

        for error in errors:
            deployment = error.deployment_info

            # 1. Check max retries exceeded → give_up
            if deployment.phase_attempts >= SERVICE_MAX_RETRIES:
                give_up_errors.append(error)
                continue

            # 2. Check timeout exceeded → expired
            lifecycle = deployment.deployment_info.state.lifecycle
            if _is_transition_timed_out(deployment.phase_started_at, lifecycle, current_dbtime):
                expired_errors.append(error)
                continue

            # 3. Default → need_retry
            retry_errors.append(error)

        return FailureClassificationResult(
            give_up=give_up_errors,
            expired=expired_errors,
            need_retry=retry_errors,
        )

    @staticmethod
    def _build_lifecycle_notification_event(
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
