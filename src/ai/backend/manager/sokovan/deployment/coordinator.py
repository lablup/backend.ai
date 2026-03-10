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
    DeploymentLifecycleStatus,
    DeploymentSubStatus,
    DeploymentSubStep,
)
from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
from ai.backend.manager.defs import SERVICE_MAX_RETRIES, LockID
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import (
    DeploymentConditions,
    DeploymentRepository,
)
from ai.backend.manager.repositories.deployment.creators import (
    EndpointLifecycleBatchUpdaterSpec,
)
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
    DeploymentHandler,
    DestroyingDeploymentHandler,
    ReconcileDeploymentHandler,
    ScalingDeploymentHandler,
)
from .strategy.applier import StrategyResultApplier
from .strategy.blue_green import BlueGreenStrategy
from .strategy.evaluator import DeploymentStrategyEvaluator
from .strategy.rolling_update import RollingUpdateStrategy
from .strategy.types import DeploymentStrategyRegistry
from .types import DeploymentExecutionError, DeploymentExecutionResult, DeploymentLifecycleType

log = BraceStyleAdapter(logging.getLogger(__name__))

# Handler registry key: (lifecycle_type, sub_step).
# sub_step is None for handlers that don't filter by sub-step.
type HandlerKey = tuple[DeploymentLifecycleType, DeploymentSubStep | None]

# Timeout thresholds for deployment lifecycle statuses (seconds).
DEPLOYMENT_STATUS_TIMEOUT_MAP: dict[EndpointLifecycle, float] = {
    EndpointLifecycle.DEPLOYING: 1800.0,  # 30 minutes
}


@dataclass
class _PhaseInfo:
    """Phase tracking info from scheduling history."""

    attempts: int = 0
    started_at: datetime | None = None


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
class HandlerRegistry:
    """Registry holding flat handler map."""

    handlers: dict[HandlerKey, DeploymentHandler]

    def sub_steps_for(self, lifecycle_type: DeploymentLifecycleType) -> list[DeploymentSubStep]:
        """Derive sub-steps from registered handler keys."""
        return [
            sub_step
            for lt, sub_step in self.handlers
            if lt == lifecycle_type and sub_step is not None
        ]


@dataclass
class DeploymentTaskSpec:
    """Specification for a deployment lifecycle periodic task."""

    lifecycle_type: DeploymentLifecycleType
    sub_step: DeploymentSubStep | None = None
    short_interval: float | None = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def _sub_step_value(self) -> str | None:
        return self.sub_step.value if self.sub_step is not None else None

    def create_if_needed_event(self) -> DoDeploymentLifecycleIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoDeploymentLifecycleIfNeededEvent(
            self.lifecycle_type.value, sub_step=self._sub_step_value()
        )

    def create_process_event(self) -> DoDeploymentLifecycleEvent:
        """Create event for forced processing."""
        return DoDeploymentLifecycleEvent(
            self.lifecycle_type.value, sub_step=self._sub_step_value()
        )

    @property
    def _suffix(self) -> str:
        base = self.lifecycle_type.value
        if self.sub_step is not None:
            return f"{base}_{self.sub_step.value}"
        return base

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"deployment_process_if_needed_{self._suffix}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
        return f"deployment_process_{self._suffix}"


class DeploymentCoordinator:
    """Coordinates deployment-related operations.

    Handlers are registered flat with a ``(lifecycle_type, sub_step)`` key.
    ``sub_step=None`` means the handler matches all deployments of that lifecycle.

    A lifecycle type may optionally have a **pre-step** that runs once on all
    deployments of that lifecycle before handlers are dispatched.
    """

    _valkey_schedule: ValkeyScheduleClient
    _deployment_controller: DeploymentController
    _deployment_repository: DeploymentRepository
    _registry: HandlerRegistry
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
        self._registry = self._init_handlers(executor)

    @staticmethod
    def _init_deployment_strategy_registry() -> DeploymentStrategyRegistry:
        """Initialize the strategy registry with all supported deployment strategies."""
        registry = DeploymentStrategyRegistry()
        registry.register(DeploymentStrategy.ROLLING, RollingUpdateStrategy, RollingUpdateSpec)
        registry.register(DeploymentStrategy.BLUE_GREEN, BlueGreenStrategy, BlueGreenSpec)
        return registry

    def _init_handlers(self, executor: DeploymentExecutor) -> HandlerRegistry:
        """Initialize the flat handler registry.

        Registry keys are derived from each handler's ``target_statuses()``.
        """
        strategy_registry = self._init_deployment_strategy_registry()
        evaluator = DeploymentStrategyEvaluator(
            deployment_repo=self._deployment_repository,
            strategy_registry=strategy_registry,
        )
        applier = StrategyResultApplier(deployment_repo=self._deployment_repository)

        handler_list: list[tuple[DeploymentLifecycleType, DeploymentHandler]] = [
            # -- simple lifecycle handlers --
            (
                DeploymentLifecycleType.CHECK_PENDING,
                CheckPendingDeploymentHandler(
                    deployment_executor=executor,
                    deployment_controller=self._deployment_controller,
                ),
            ),
            (
                DeploymentLifecycleType.CHECK_REPLICA,
                CheckReplicaDeploymentHandler(
                    deployment_executor=executor,
                    deployment_controller=self._deployment_controller,
                ),
            ),
            (
                DeploymentLifecycleType.SCALING,
                ScalingDeploymentHandler(
                    deployment_executor=executor,
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                ),
            ),
            (
                DeploymentLifecycleType.RECONCILE,
                ReconcileDeploymentHandler(
                    deployment_executor=executor,
                    deployment_controller=self._deployment_controller,
                ),
            ),
            (
                DeploymentLifecycleType.DESTROYING,
                DestroyingDeploymentHandler(
                    deployment_executor=executor,
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                ),
            ),
            # -- DEPLOYING sub-step handlers --
            (
                DeploymentLifecycleType.DEPLOYING,
                DeployingProvisioningHandler(
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                    evaluator=evaluator,
                    applier=applier,
                ),
            ),
            (
                DeploymentLifecycleType.DEPLOYING,
                DeployingProgressingHandler(
                    deployment_controller=self._deployment_controller,
                    route_controller=self._route_controller,
                    evaluator=evaluator,
                    applier=applier,
                ),
            ),
        ]

        handlers: dict[HandlerKey, DeploymentHandler] = {}
        for lifecycle_type, handler in handler_list:
            key = self._derive_handler_key(lifecycle_type, handler)
            handlers[key] = handler

        return HandlerRegistry(handlers=handlers)

    @staticmethod
    def _derive_handler_key(
        lifecycle_type: DeploymentLifecycleType,
        handler: DeploymentHandler,
    ) -> HandlerKey:
        """Derive a registry key from the handler's target_statuses().

        Uses the first entry's sub_status as the key.  Handlers that target
        multiple sub-steps (e.g. PROGRESSING handler handling COMPLETED and
        ROLLED_BACK too) are keyed by their primary sub-step.
        """
        statuses = handler.target_statuses()
        if not statuses:
            return (lifecycle_type, None)
        first_sub = statuses[0].sub_status
        if isinstance(first_sub, DeploymentSubStep):
            return (lifecycle_type, first_sub)
        return (lifecycle_type, None)

    async def process_deployment_lifecycle(
        self,
        lifecycle_type: DeploymentLifecycleType,
        sub_step: DeploymentSubStep | None = None,
    ) -> None:
        handler = self._registry.handlers.get((lifecycle_type, sub_step))
        if handler is None:
            log.warning(
                "No handler for deployment lifecycle ({}, {})",
                lifecycle_type.value,
                sub_step,
            )
            return

        lock_id = handler.lock_id
        async with AsyncExitStack() as stack:
            if lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(lock_id, lock_lifetime))
            await self._run_handler(handler, lifecycle_type)

    async def _run_handler(
        self,
        handler: DeploymentHandler,
        lifecycle_type: DeploymentLifecycleType,
    ) -> None:
        """Run a single handler: fetch filtered deployments → execute → transitions → post_process."""
        target_statuses = handler.target_statuses()
        lifecycles = list({s.lifecycle for s in target_statuses})
        sub_steps = [
            s.sub_status for s in target_statuses if isinstance(s.sub_status, DeploymentSubStep)
        ]
        deployments = await self._deployment_repository.get_endpoints_by_statuses(
            lifecycles,
            sub_steps=sub_steps or None,
        )
        if not deployments:
            log.trace("No deployments to process for handler: {}", handler.name())
            return
        log.info("handler: {} - processing {} deployments", handler.name(), len(deployments))

        deployment_ids = [d.id for d in deployments]

        # Build phase info from scheduling history (kept separate from DeploymentInfo)
        handler_name = handler.name()
        history_map = await self._deployment_repository.get_last_deployment_histories(
            deployment_ids
        )
        phase_map: dict[UUID, _PhaseInfo] = {}
        for deployment in deployments:
            history = history_map.get(deployment.id)
            if history and history.phase == handler_name:
                phase_map[deployment.id] = _PhaseInfo(
                    attempts=history.attempts,
                    started_at=history.created_at,
                )
            else:
                phase_map[deployment.id] = _PhaseInfo()

        with DeploymentRecorderContext.scope(handler_name, entity_ids=deployment_ids) as pool:
            result = await handler.execute(deployments)
            all_records = pool.build_all_records()
            await self._handle_status_transitions(handler, result, all_records, phase_map)

        try:
            await handler.post_process(result)
        except Exception as e:
            log.error("Error during post-processing for {}: {}", handler.name(), e)

    async def _handle_status_transitions(
        self,
        handler: DeploymentHandler,
        result: DeploymentExecutionResult,
        records: Mapping[UUID, ExecutionRecord],
        phase_map: dict[UUID, _PhaseInfo],
    ) -> None:
        """Handle status transitions with history recording.

        Classifies failures into need_retry/expired/give_up using scheduling
        history, then applies per-category transitions. All transitions are
        processed in a single transaction.
        """
        handler_name = handler.name()
        target_statuses = handler.target_statuses()
        target_lifecycles = list({s.lifecycle for s in target_statuses})

        batch_updaters: list[BatchUpdater[EndpointRow]] = []
        all_history_specs: list[DeploymentHistoryCreatorSpec] = []
        notification_events: list[NotificationTriggeredEvent] = []
        timestamp_now = datetime.now(UTC).isoformat()

        transitions = handler.status_transitions()

        # Success transitions (None = stay in current state)
        if transitions.success is not None and result.successes:
            t = self._build_success_transition(
                handler_name=handler_name,
                deployments=result.successes,
                lifecycle_status=transitions.success,
                target_lifecycles=target_lifecycles,
                records=records,
                timestamp_now=timestamp_now,
            )
            batch_updaters.append(t.updater)
            all_history_specs.extend(t.history_specs)
            notification_events.extend(t.notification_events)

        # Failure transitions
        if result.errors:
            current_time = await self._deployment_repository.get_db_now()
            classified = self._classify_failures(result.errors, phase_map, current_time)

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
                t = self._build_failure_transition(
                    handler_name=handler_name,
                    errors=errors,
                    lifecycle_status=lifecycle_status,
                    scheduling_result=scheduling_result,
                    target_lifecycles=target_lifecycles,
                    records=records,
                    timestamp_now=timestamp_now,
                    transition_label=label,
                )
                batch_updaters.append(t.updater)
                all_history_specs.extend(t.history_specs)
                notification_events.extend(t.notification_events)

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
            spec=EndpointLifecycleBatchUpdaterSpec(
                lifecycle_stage=lifecycle_status.lifecycle,
                sub_step=lifecycle_status.sub_status,
            ),
            conditions=[
                DeploymentConditions.by_ids(endpoint_ids),
                DeploymentConditions.by_lifecycle_stages(target_lifecycles),
            ],
        )

    def _build_success_transition(
        self,
        *,
        handler_name: str,
        deployments: list[DeploymentInfo],
        lifecycle_status: DeploymentLifecycleStatus,
        target_lifecycles: list[EndpointLifecycle],
        records: Mapping[UUID, ExecutionRecord],
        timestamp_now: str,
    ) -> _TransitionResult:
        next_lifecycle = lifecycle_status.lifecycle
        endpoint_ids = [d.id for d in deployments]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=d.id,
                phase=handler_name,
                result=SchedulingResult.SUCCESS,
                message=f"{handler_name} completed successfully",
                from_status=d.state.lifecycle,
                to_status=next_lifecycle,
                sub_steps=self._build_history_sub_steps(
                    d.id, records, d.sub_step, SchedulingResult.SUCCESS
                ),
            )
            for d in deployments
        ]
        events = [
            self._build_lifecycle_notification_event(
                deployment=d,
                from_status=d.state.lifecycle,
                to_status=next_lifecycle,
                transition_result="success",
                timestamp=timestamp_now,
            )
            for d in deployments
        ]
        updater = self._build_lifecycle_updater(endpoint_ids, lifecycle_status, target_lifecycles)
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
        target_lifecycles: list[EndpointLifecycle],
        records: Mapping[UUID, ExecutionRecord],
        timestamp_now: str,
        transition_label: str,
    ) -> _TransitionResult:
        next_lifecycle = lifecycle_status.lifecycle
        endpoint_ids = [e.deployment_info.id for e in errors]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=e.deployment_info.id,
                phase=handler_name,
                result=scheduling_result,
                message=e.reason,
                from_status=e.deployment_info.state.lifecycle,
                to_status=next_lifecycle,
                error_code=e.error_code,
                sub_steps=self._build_history_sub_steps(
                    e.deployment_info.id, records, e.deployment_info.sub_step, scheduling_result
                ),
            )
            for e in errors
        ]
        events = [
            self._build_lifecycle_notification_event(
                deployment=e.deployment_info,
                from_status=e.deployment_info.state.lifecycle,
                to_status=next_lifecycle,
                transition_result=transition_label,
                timestamp=timestamp_now,
            )
            for e in errors
        ]
        updater = self._build_lifecycle_updater(endpoint_ids, lifecycle_status, target_lifecycles)
        return _TransitionResult(
            updater=updater,
            history_specs=history_specs,
            notification_events=events,
        )

    @staticmethod
    def _classify_failures(
        errors: list[DeploymentExecutionError],
        phase_map: dict[UUID, _PhaseInfo],
        current_time: datetime,
    ) -> FailureClassificationResult:
        """Classify failures into give_up, expired, need_retry.

        Classification priority (first match wins):
        1. give_up: phase_attempts >= SERVICE_MAX_RETRIES
        2. expired: timeout exceeded
        3. need_retry: default

        Args:
            errors: Failed deployment execution errors
            phase_map: Phase tracking info (attempts, started_at) per deployment
            current_time: Current database time for timeout comparison

        Returns:
            FailureClassificationResult with give_up, expired, need_retry lists
        """
        give_up_errors: list[DeploymentExecutionError] = []
        expired_errors: list[DeploymentExecutionError] = []
        retry_errors: list[DeploymentExecutionError] = []

        for error in errors:
            deployment_id = error.deployment_info.id
            phase = phase_map.get(deployment_id, _PhaseInfo())

            # 1. Check max retries exceeded → give_up
            if phase.attempts >= SERVICE_MAX_RETRIES:
                give_up_errors.append(error)
                continue

            # 2. Check timeout exceeded → expired
            if phase.started_at:
                lifecycle = error.deployment_info.state.lifecycle
                timeout = DEPLOYMENT_STATUS_TIMEOUT_MAP.get(lifecycle)
                if timeout:
                    # Normalise both to UTC to avoid timezone-naive vs -aware
                    # comparison errors (DB may return either depending on driver).
                    current_utc = (
                        current_time.astimezone(UTC)
                        if current_time.tzinfo
                        else current_time.replace(tzinfo=UTC)
                    )
                    phase_started_utc = (
                        phase.started_at.astimezone(UTC)
                        if phase.started_at.tzinfo
                        else phase.started_at.replace(tzinfo=UTC)
                    )
                    elapsed = (current_utc - phase_started_utc).total_seconds()
                    if elapsed > timeout:
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

    @staticmethod
    def _build_lifecycle_notification_event(
        deployment: DeploymentInfo,
        from_status: EndpointLifecycle,
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
            from_status=from_status.value,
            to_status=to_status.value,
            transition_result=transition_result,
            event_timestamp=timestamp,
        )
        return NotificationTriggeredEvent(
            rule_type=NotificationRuleType.ENDPOINT_LIFECYCLE_CHANGED.value,
            timestamp=datetime.now(UTC),
            notification_data=message.model_dump(),
        )

    async def process_if_needed(
        self,
        lifecycle_type: DeploymentLifecycleType,
        sub_step: DeploymentSubStep | None = None,
    ) -> None:
        """Process deployment lifecycle operation if needed (based on internal state)."""
        sub_step_value = sub_step.value if sub_step is not None else None
        if not await self._valkey_schedule.load_and_delete_deployment_mark(
            lifecycle_type.value, sub_step_value
        ):
            return
        await self.process_deployment_lifecycle(lifecycle_type, sub_step)

    def _create_task_specs(self) -> list[DeploymentTaskSpec]:
        """Create task specifications for all deployment lifecycle types.

        Simple lifecycles get a single spec with sub_step=None.
        Lifecycles with sub-step handlers get one spec per sub-step.
        """
        specs: list[DeploymentTaskSpec] = [
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
        # Deploying — one task per sub-step
        for sub_step in self._registry.sub_steps_for(DeploymentLifecycleType.DEPLOYING):
            specs.append(
                DeploymentTaskSpec(
                    DeploymentLifecycleType.DEPLOYING,
                    sub_step=sub_step,
                    short_interval=5.0,
                    long_interval=30.0,
                    initial_delay=10.0,
                )
            )
        return specs

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
