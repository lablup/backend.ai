import asyncio
import logging
from collections.abc import Mapping, Sequence
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.common.events.event_types.schedule.anycast import (
    DoSokovanProcessIfNeededEvent,
    DoSokovanProcessScheduleEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.common.types import AccessKey, AgentId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    StatusTransitions,
    TransitionStatus,
)
from ai.backend.manager.defs import SERVICE_MAX_RETRIES
from ai.backend.manager.metrics.scheduler import SchedulerOperationMetricObserver
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.pagination import NoPagination, OffsetPagination
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.scheduler.options import KernelConditions, SessionConditions
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.scheduler.updaters import SessionStatusBatchUpdaterSpec
from ai.backend.manager.repositories.scheduling_history.creators import (
    SessionSchedulingHistoryCreatorSpec,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.data import (
    KernelCreationInfo,
    PromotionSpec,
    SessionWithKernels,
)
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.sokovan.scheduler.scheduler import SchedulerComponents
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import DistributedLockFactory

from .factory import CoordinatorHandlers
from .handlers import SessionLifecycleHandler
from .handlers.kernel import KernelLifecycleHandler
from .handlers.observer import KernelObserver
from .hooks.registry import HookRegistry
from .kernel import KernelStateEngine
from .post_processors import (
    KernelPostProcessor,
    KernelPostProcessorContext,
    PostProcessor,
    PostProcessorContext,
    create_kernel_post_processors,
    create_session_post_processors,
)
from .recorder import SessionRecorderContext
from .results import (
    KernelExecutionResult,
    KernelStatusTransitions,
    SessionExecutionResult,
    SessionTransitionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

# Status timeout thresholds (in seconds) for failure classification
# Sessions exceeding these times in a status are classified as 'expired'
STATUS_TIMEOUT_MAP: dict[SessionStatus, float] = {
    SessionStatus.PREPARING: 900.0,  # 15 minutes
    SessionStatus.PULLING: 900.0,  # 15 minutes
    SessionStatus.CREATING: 600.0,  # 10 minutes
}

# Batch size for observer kernel processing
_OBSERVER_BATCH_SIZE: Final[int] = 500


@dataclass
class SchedulerTaskSpec:
    """Specification for a scheduler's periodic task."""

    schedule_type: ScheduleType
    short_interval: float | None = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoSokovanProcessIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoSokovanProcessIfNeededEvent(self.schedule_type.value)

    def create_process_event(self) -> DoSokovanProcessScheduleEvent:
        """Create event for forced processing."""
        return DoSokovanProcessScheduleEvent(self.schedule_type.value)

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"sokovan_process_if_needed_{self.schedule_type.value}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
        return f"sokovan_process_schedule_{self.schedule_type.value}"


@dataclass
class HookExecutionResult:
    """Result of hook execution for sessions transitioning to a new status.

    Contains both the session transition info and full session data
    for sessions that successfully passed hooks.
    """

    successful_sessions: list[SessionTransitionInfo]
    """Sessions that passed hooks and should proceed with transition."""

    full_session_data: list[SessionWithKernels]
    """Full session+kernel data for successful sessions (for occupied_slots calculation)."""


@dataclass
class FailureClassificationResult:
    """Result of classifying failures into give_up, expired, and need_retry.

    Classification priority (first match wins):
    1. give_up: phase_attempts >= SERVICE_MAX_RETRIES
    2. expired: status_changed elapsed > STATUS_TIMEOUT_MAP threshold
    3. need_retry: default (can be retried)
    """

    give_up: list[SessionTransitionInfo]
    """Sessions that exceeded max retries - should transition to give_up status."""

    expired: list[SessionTransitionInfo]
    """Sessions that exceeded timeout threshold - should transition to expired status."""

    need_retry: list[SessionTransitionInfo]
    """Sessions that can be retried - should transition to need_retry status."""


class ScheduleCoordinator:
    """
    Coordinate scheduling operations based on scheduling needs.
    Handles the actual scheduling logic and state management.
    """

    _valkey_schedule: ValkeyScheduleClient
    _components: SchedulerComponents
    _handlers: CoordinatorHandlers
    _scheduling_controller: SchedulingController
    _repository: SchedulerRepository
    _operation_metrics: SchedulerOperationMetricObserver
    _kernel_state_engine: KernelStateEngine
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer
    _hook_registry: HookRegistry
    _post_processors: Sequence[PostProcessor]
    _kernel_post_processors: Sequence[KernelPostProcessor]

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        components: SchedulerComponents,
        handlers: CoordinatorHandlers,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
    ) -> None:
        self._valkey_schedule = valkey_schedule
        self._components = components
        self._handlers = handlers
        self._scheduling_controller = scheduling_controller
        self._repository = components.repository
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = components.config_provider
        self._operation_metrics = SchedulerOperationMetricObserver.instance()

        # Initialize kernel state engine with the component's repository
        self._kernel_state_engine = KernelStateEngine(components.repository)

        # Initialize hook registry from components
        self._hook_registry = components.hook_registry

        # Initialize post-processors for session handlers
        self._post_processors = create_session_post_processors(
            scheduling_controller,
            components.repository,
        )

        # Initialize post-processors for kernel handlers
        self._kernel_post_processors = create_kernel_post_processors(
            scheduling_controller,
        )

    async def process_lifecycle_schedule(
        self,
        schedule_type: ScheduleType,
    ) -> bool:
        """Process a lifecycle schedule type using the DeploymentCoordinator pattern.

        This method processes each scaling group independently:
        1. Iterates over all schedulable scaling groups
        2. For each scaling group:
           - Creates a SessionRecorderContext for the scaling group
           - Queries sessions based on handler's target_statuses() and target_kernel_statuses()
           - Executes handler logic
           - Applies status transitions immediately
           - Emits metrics per scaling group
           - Runs post-processing per scaling group

        This per-scaling-group approach prevents accumulating too many sessions
        in memory and ensures status updates are applied promptly.

        Args:
            schedule_type: Type of scheduling operation

        Returns:
            True if operation was performed, False otherwise
        """
        # Check kernel observers first (no state transitions)
        kernel_observer = self._handlers.kernel_observers.get(schedule_type)
        if kernel_observer:
            return await self._process_observer_schedule(schedule_type, kernel_observer)

        # Check promotion specs, then kernel handlers, then lifecycle handlers
        promotion_spec = self._handlers.promotion_specs.get(schedule_type)
        if promotion_spec:
            return await self._process_promotion_schedule(schedule_type, promotion_spec)

        kernel_handler = self._handlers.kernel_handlers.get(schedule_type)
        if kernel_handler:
            return await self._process_kernel_schedule(schedule_type, kernel_handler)

        lifecycle_handler = self._handlers.lifecycle_handlers.get(schedule_type)
        if lifecycle_handler:
            return await self._process_lifecycle_handler_schedule(schedule_type, lifecycle_handler)

        log.warning("No handler for schedule type: {}", schedule_type.value)
        return False

    async def _process_lifecycle_handler_schedule(
        self,
        schedule_type: ScheduleType,
        handler: SessionLifecycleHandler,
    ) -> bool:
        """Process a lifecycle handler schedule type."""
        try:
            log.debug("Processing lifecycle schedule type: {}", schedule_type.value)

            async with AsyncExitStack() as stack:
                stack.enter_context(self._operation_metrics.measure_operation(handler.name()))

                # Acquire lock if needed
                if handler.lock_id is not None:
                    lock_lifetime = (
                        self._config_provider.config.manager.session_schedule_lock_lifetime
                    )
                    await stack.enter_async_context(
                        self._lock_factory(handler.lock_id, lock_lifetime)
                    )

                # Process each scaling group in parallel
                scaling_groups = await self._repository.get_schedulable_scaling_groups()

                results = await asyncio.gather(
                    *[
                        self._process_scaling_group(handler, schedule_type, scaling_group)
                        for scaling_group in scaling_groups
                    ],
                    return_exceptions=True,
                )

                # Log any exceptions that occurred during parallel processing
                for scaling_group, result in zip(scaling_groups, results, strict=True):
                    if isinstance(result, BaseException):
                        log.error(
                            "Error processing scaling group {} for {}: {}",
                            scaling_group,
                            schedule_type.value,
                            result,
                        )

            return True

        except Exception as e:
            log.exception(
                "Error processing lifecycle schedule type {}: {}",
                schedule_type.value,
                e,
            )
            raise

    async def _process_promotion_schedule(
        self,
        schedule_type: ScheduleType,
        spec: PromotionSpec,
    ) -> bool:
        """Process a promotion spec schedule type.

        Promotion specs define query conditions and target status declaratively.
        The Coordinator processes sessions matching the spec directly.
        """
        try:
            log.debug("Processing promotion schedule type: {}", schedule_type.value)

            with self._operation_metrics.measure_operation(spec.name):
                # Process each scaling group in parallel
                scaling_groups = await self._repository.get_schedulable_scaling_groups()

                results = await asyncio.gather(
                    *[
                        self._process_promotion_scaling_group(spec, schedule_type, scaling_group)
                        for scaling_group in scaling_groups
                    ],
                    return_exceptions=True,
                )

                # Log any exceptions that occurred during parallel processing
                for scaling_group, result in zip(scaling_groups, results, strict=True):
                    if isinstance(result, BaseException):
                        log.error(
                            "Error processing scaling group {} for {}: {}",
                            scaling_group,
                            schedule_type.value,
                            result,
                        )

            return True

        except Exception as e:
            log.exception(
                "Error processing promotion schedule type {}: {}",
                schedule_type.value,
                e,
            )
            raise

    async def _process_kernel_schedule(
        self,
        schedule_type: ScheduleType,
        handler: KernelLifecycleHandler,
    ) -> bool:
        """Process a kernel handler schedule type.

        Kernel handlers operate on kernels directly. The flow:
        1. Query sessions based on handler's target_kernel_statuses
        2. Extract kernels from sessions
        3. Execute handler logic
        4. Apply kernel status transitions based on result
        """
        try:
            log.debug("Processing kernel schedule type: {}", schedule_type.value)

            async with AsyncExitStack() as stack:
                stack.enter_context(self._operation_metrics.measure_operation(handler.name()))

                # Acquire lock if needed
                if handler.lock_id is not None:
                    lock_lifetime = (
                        self._config_provider.config.manager.session_schedule_lock_lifetime
                    )
                    await stack.enter_async_context(
                        self._lock_factory(handler.lock_id, lock_lifetime)
                    )

                # Process each scaling group in parallel
                scaling_groups = await self._repository.get_schedulable_scaling_groups()

                results = await asyncio.gather(
                    *[
                        self._process_kernel_scaling_group(handler, schedule_type, scaling_group)
                        for scaling_group in scaling_groups
                    ],
                    return_exceptions=True,
                )

                # Log any exceptions that occurred during parallel processing
                for scaling_group, result in zip(scaling_groups, results, strict=True):
                    if isinstance(result, BaseException):
                        log.error(
                            "Error processing scaling group {} for {}: {}",
                            scaling_group,
                            schedule_type.value,
                            result,
                        )

            return True

        except Exception as e:
            log.exception(
                "Error processing kernel schedule type {}: {}",
                schedule_type.value,
                e,
            )
            raise

    async def _process_observer_schedule(
        self,
        schedule_type: ScheduleType,
        observer: KernelObserver,
    ) -> bool:
        """Process a kernel observer schedule type.

        Observers do not change kernel state - they only collect data.
        Used for fair share usage tracking, metrics collection, etc.

        Args:
            schedule_type: Type of scheduling operation
            observer: The kernel observer to execute

        Returns:
            True if operation was performed, False otherwise
        """
        try:
            log.debug(
                "[Coordinator] Processing observer schedule: type={}, observer={}",
                schedule_type.value,
                observer.name(),
            )

            async with AsyncExitStack() as stack:
                stack.enter_context(self._operation_metrics.measure_operation(observer.name()))

                # Process each scaling group in parallel
                scaling_groups = await self._repository.get_schedulable_scaling_groups()

                log.debug(
                    "[Coordinator] Found {} scaling groups to observe: {}",
                    len(scaling_groups),
                    scaling_groups,
                )

                results = await asyncio.gather(
                    *[
                        self._process_observer_scaling_group(observer, scaling_group)
                        for scaling_group in scaling_groups
                    ],
                    return_exceptions=True,
                )

                # Log any exceptions that occurred during parallel processing
                for scaling_group, result in zip(scaling_groups, results, strict=True):
                    if isinstance(result, BaseException):
                        log.error(
                            "Error observing scaling group {} for {}: {}",
                            scaling_group,
                            schedule_type.value,
                            result,
                        )

            log.debug("[Coordinator] Observer schedule {} completed", schedule_type.value)
            return True

        except Exception as e:
            log.exception(
                "Error processing observer schedule type {}: {}",
                schedule_type.value,
                e,
            )
            raise

    async def _process_observer_scaling_group(
        self,
        observer: KernelObserver,
        scaling_group: str,
    ) -> None:
        """Process a single scaling group for the given observer.

        This method:
        1. Queries kernels using observer's query condition
        2. Processes kernels in batches with pagination
        3. Executes observer logic (no state transitions)
        4. Emits metrics

        Args:
            observer: The kernel observer to execute
            scaling_group: The scaling group to process
        """
        log.debug(
            "[Coordinator] Processing observer {} for scaling_group={}",
            observer.name(),
            scaling_group,
        )
        condition = observer.get_query_condition(scaling_group)

        # Process in batches with pagination for large result sets
        offset = 0
        total_observed = 0

        while True:
            querier = BatchQuerier(
                pagination=OffsetPagination(limit=_OBSERVER_BATCH_SIZE, offset=offset),
                conditions=[condition],
            )

            kernel_result = await self._repository.search_kernels_for_handler(querier)

            log.debug(
                "[Coordinator] Observer {} batch: offset={}, items_count={}, has_next_page={}",
                observer.name(),
                offset,
                len(kernel_result.items),
                kernel_result.has_next_page,
            )

            if not kernel_result.items:
                log.debug("[Coordinator] Observer {} no items found, exiting loop", observer.name())
                break

            # Execute observer logic (no status transitions)
            result = await observer.observe(scaling_group, kernel_result.items)
            total_observed += result.observed_count

            # Check if there are more pages
            if not kernel_result.has_next_page:
                break

            offset += _OBSERVER_BATCH_SIZE

        log.debug(
            "[Coordinator] Observer {} completed: total_observed={}",
            observer.name(),
            total_observed,
        )

        # Emit metrics (total observed count across all batches)
        if total_observed > 0:
            self._operation_metrics.observe_success(
                operation=observer.name(),
                count=total_observed,
            )

    async def _process_kernel_scaling_group(
        self,
        handler: KernelLifecycleHandler,
        _schedule_type: ScheduleType,
        scaling_group: str,
    ) -> None:
        """Process a single scaling group for the given kernel handler.

        This method:
        1. Queries sessions to get kernels for the handler
        2. Extracts kernels matching the target status
        3. Executes handler logic
        4. Applies kernel status transitions

        Args:
            handler: The kernel handler to execute
            schedule_type: Type of scheduling operation
            scaling_group: The scaling group to process
        """
        # Build querier with kernel conditions
        target_kernel_statuses = handler.target_kernel_statuses()

        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                KernelConditions.by_scaling_group(scaling_group),
                KernelConditions.by_statuses(target_kernel_statuses),
            ],
        )

        kernel_result = await self._repository.search_kernels_for_handler(querier)

        if not kernel_result.items:
            return

        # Execute handler logic with kernels
        result = await handler.execute(scaling_group, kernel_result.items)

        # Apply kernel status transitions based on handler's status_transitions
        await self._handle_kernel_result(handler, result)

        # Emit metrics per scaling group
        self._operation_metrics.observe_success(
            operation=handler.name(),
            count=result.success_count(),
        )

        # Run kernel post-processors
        if result.has_transitions():
            transitions = handler.status_transitions()
            target_statuses = self._collect_kernel_target_statuses(transitions, result)
            try:
                await self._run_kernel_post_processors(result, target_statuses)
            except Exception as e:
                log.error(
                    "Error during kernel post-processing for scaling group {}: {}",
                    scaling_group,
                    e,
                )

    async def _handle_kernel_result(
        self,
        handler: KernelLifecycleHandler,
        result: KernelExecutionResult,
    ) -> None:
        """Apply kernel status transitions based on handler result.

        Unlike session handlers which use BEP-1030 pattern with multiple outcome paths,
        kernel handlers have simpler success/failure transitions.

        Args:
            handler: The kernel handler that produced the result
            result: The execution result with successes and failures
        """
        handler_name = handler.name()
        transitions = handler.status_transitions()

        # Handle failures - apply failure transition (typically to TERMINATED)
        if result.failures and transitions.failure:
            for failure in result.failures:
                await self._kernel_state_engine.mark_kernel_terminated(
                    failure.kernel_id,
                    failure.reason or "kernel_handler_failure",
                )
            log.debug(
                "{}: Terminated {} kernels",
                handler_name,
                len(result.failures),
            )

        # Handle successes - typically no status change (success means kernel is healthy)
        # Success transition is usually None, meaning no status change needed
        if result.successes:
            log.debug(
                "{}: {} kernels processed successfully (no status change)",
                handler_name,
                len(result.successes),
            )

    async def _process_scaling_group(
        self,
        handler: SessionLifecycleHandler,
        schedule_type: ScheduleType,
        scaling_group: str,
    ) -> None:
        """Process a single scaling group for the given handler.

        This method handles all processing for one scaling group:
        - Creates a SessionRecorderContext scoped to this scaling group
        - Queries and processes sessions
        - Applies status transitions
        - Emits metrics
        - Runs post-processing

        Args:
            handler: The lifecycle handler to execute
            schedule_type: Type of scheduling operation
            scaling_group: The scaling group to process
        """
        # Query sessions for this handler in this scaling group
        sessions = await self._repository.get_sessions_for_handler(
            scaling_group,
            handler.target_statuses(),
            handler.target_kernel_statuses(),
        )

        if not sessions:
            return

        # Extract session IDs for recorder entity_ids
        session_ids = [s.session_info.identity.id for s in sessions]

        # Populate phase_attempts and phase_started_at from scheduling history for failure classification
        # Get last history records (regardless of phase), then compare phase at application level
        history_map = await self._repository.get_last_session_histories(session_ids)
        handler_name = handler.name()
        for session in sessions:
            history = history_map.get(session.session_info.identity.id)
            # Only use history data if the last history is for the current phase
            if history and history.phase == handler_name:
                session.phase_attempts = history.attempts
                session.phase_started_at = history.created_at
            else:
                session.phase_attempts = 0
                session.phase_started_at = None

        # Create recorder scoped to this scaling group
        recorder_scope = f"{schedule_type.value}:{scaling_group}"
        with SessionRecorderContext.scope(recorder_scope, entity_ids=session_ids) as pool:
            # Execute handler logic
            result = await handler.execute(scaling_group, sessions)

            # Get recorded steps for history
            all_records = pool.build_all_records()

            # Apply status transitions immediately for this scaling group (BEP-1030)
            classified = await self._handle_result(handler, result, all_records, sessions)

            # Emit metrics per scaling group
            self._operation_metrics.observe_success(
                operation=handler.name(),
                count=result.success_count(),
            )

            # Common post-process: mark next schedule and invalidate cache
            if result.has_transitions():
                transitions = handler.status_transitions()
                # Collect all target statuses from success and classified failures
                target_statuses = self._collect_target_statuses(
                    transitions, result.successes, classified
                )
                try:
                    await self._run_post_processors(result, target_statuses)
                except Exception as e:
                    log.error(
                        "Error during common post-processing for scaling group {}: {}",
                        scaling_group,
                        e,
                    )

            # Log recorded steps for this scaling group
            if all_records:
                log.debug(
                    "Recorded {} sessions with execution records for {} in scaling group {}",
                    len(all_records),
                    schedule_type.value,
                    scaling_group,
                )

    async def _process_promotion_scaling_group(
        self,
        spec: PromotionSpec,
        schedule_type: ScheduleType,
        scaling_group: str,
    ) -> None:
        """Process a single scaling group for the given promotion spec.

        This method handles all processing for one scaling group using
        promotion spec semantics (ALL/ANY/NOT_ANY kernel matching).

        Args:
            spec: The promotion spec to process
            schedule_type: Type of scheduling operation
            scaling_group: The scaling group to process
        """
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                SessionConditions.by_scaling_group(scaling_group),
                SessionConditions.by_statuses(spec.target_statuses),
                SessionConditions.by_kernel_match(
                    spec.target_kernel_statuses,
                    spec.kernel_match_type,
                ),
            ],
        )

        # Query sessions (only session data, no kernels)
        session_infos = await self._repository.search_sessions_for_handler(querier)

        if not session_infos:
            return

        session_ids = [info.identity.id for info in session_infos]

        # Create recorder scoped to this scaling group
        recorder_scope = f"{schedule_type.value}:{scaling_group}"
        with SessionRecorderContext.scope(recorder_scope, entity_ids=session_ids) as pool:
            # Build transition info from matched sessions
            with SessionRecorderContext.shared_phase(
                spec.name,
                success_detail=f"Promoting to {spec.success_status.value}",
            ):
                with SessionRecorderContext.shared_step(
                    "check_kernel_status",
                    success_detail=f"All kernels ready for {spec.success_status.value}",
                ):
                    result = SessionExecutionResult()
                    for session_info in session_infos:
                        result.successes.append(
                            SessionTransitionInfo(
                                session_id=session_info.identity.id,
                                from_status=session_info.lifecycle.status,
                                reason=spec.reason,
                                creation_id=session_info.identity.creation_id,
                                access_key=AccessKey(session_info.metadata.access_key),
                            )
                        )

            # Get recorded steps for history
            all_records = pool.build_all_records()

            # Phase 2: Apply status transitions (includes hook execution)
            await self._handle_promotion_status_transitions(spec, result, all_records)

            # Emit metrics per scaling group
            self._operation_metrics.observe_success(
                operation=spec.name,
                count=result.success_count(),
            )

            # Common post-process: mark next schedule and invalidate cache
            if result.has_transitions():
                target_statuses = {spec.success_status}
                try:
                    await self._run_post_processors(result, target_statuses)
                except Exception as e:
                    log.error(
                        "Error during common post-processing for scaling group {}: {}",
                        scaling_group,
                        e,
                    )

            # Log recorded steps for this scaling group
            if all_records:
                log.debug(
                    "Recorded {} sessions with execution records for {} in scaling group {}",
                    len(all_records),
                    schedule_type.value,
                    scaling_group,
                )

    async def _handle_promotion_status_transitions(
        self,
        spec: PromotionSpec,
        result: SessionExecutionResult,
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
        """Apply status transitions for promotion spec results.

        Promotion specs only change session status (not kernel status).
        Kernel status changes are driven by agent events, not coordinator.

        Hook execution is centralized here:
        1. Check if target status has hooks configured
        2. If hooks exist, fetch full session data and execute hooks
        3. For blocking hooks, filter out sessions where hooks failed
        4. Apply status transition for remaining sessions

        Note: Status-specific logic (e.g., occupied_slots for RUNNING) is handled
        by StatusTransitionHook in the hook registry, not here in the Coordinator.

        Args:
            spec: The promotion spec that defines the transition
            result: Execution result containing successes
            records: Mapping of session IDs to their execution records for sub_steps
        """
        if not result.successes:
            return

        # Get DB time for status transition timestamp
        current_time = await self._repository.get_db_now()

        to_status = spec.success_status
        sessions_to_transition = result.successes

        # Execute hooks if available for this status
        hook = self._hook_registry.get_hook(to_status)
        if hook:
            hook_result = await self._execute_transition_hooks(
                sessions_to_transition,
                to_status,
            )
            sessions_to_transition = hook_result.successful_sessions

        # Apply status transition for sessions that passed hooks
        if sessions_to_transition:
            # Create TransitionStatus with kernel=None (promotion doesn't change kernel status)
            transition = TransitionStatus(session=to_status, kernel=None)
            await self._apply_transition(
                spec.name,
                sessions_to_transition,
                transition,
                SchedulingResult.SUCCESS,
                records,
                current_time,
            )

            # Broadcast events for successful transitions
            await self._broadcast_transition_events(sessions_to_transition, to_status)

    async def _execute_transition_hooks(
        self,
        session_infos: list[SessionTransitionInfo],
        target_status: SessionStatus,
    ) -> HookExecutionResult:
        """Execute transition hooks for sessions moving to target_status.

        Fetches full session+kernel data, executes hooks per session,
        and returns sessions that should proceed with the transition along with
        their full session data (for occupied_slots calculation on RUNNING transition).

        All hooks are blocking - if a hook fails, the session won't transition.

        Args:
            session_infos: Sessions to execute hooks for
            target_status: The status sessions are transitioning to

        Returns:
            HookExecutionResult containing:
            - successful_sessions: SessionTransitionInfo for sessions that passed hooks
            - full_session_data: SessionWithKernels for successful sessions
        """
        if not session_infos:
            return HookExecutionResult(successful_sessions=[], full_session_data=[])

        # Fetch full session+kernel data for hook execution
        session_ids = [s.session_id for s in session_infos]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[SessionConditions.by_ids(session_ids)],
        )
        full_sessions = await self._repository.search_sessions_with_kernels_for_handler(querier)

        if not full_sessions:
            log.warning(
                "No full session data found for {} sessions transitioning to {}",
                len(session_ids),
                target_status,
            )
            return HookExecutionResult(successful_sessions=[], full_session_data=[])

        # Build session_id -> SessionTransitionInfo mapping for results
        info_map = {s.session_id: s for s in session_infos}

        # Execute hooks concurrently
        hook_coroutines = [
            self._execute_single_hook(session, target_status) for session in full_sessions
        ]
        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        # Process results - all hooks are blocking
        successful_sessions: list[SessionTransitionInfo] = []
        successful_full_sessions: list[SessionWithKernels] = []
        for session, hook_result in zip(full_sessions, hook_results, strict=True):
            session_id = session.session_info.identity.id
            original_info = info_map.get(session_id)

            if original_info is None:
                continue

            if isinstance(hook_result, BaseException):
                log.error(
                    "Hook failed for session {} transitioning to {}: {}",
                    session_id,
                    target_status,
                    hook_result,
                )
                # Hook failed - don't include in successful sessions
                continue

            successful_sessions.append(original_info)
            successful_full_sessions.append(session)

        log.info(
            "Executed on_transition hooks for {} sessions transitioning to {} ({} succeeded)",
            len(full_sessions),
            target_status,
            len(successful_sessions),
        )

        return HookExecutionResult(
            successful_sessions=successful_sessions,
            full_session_data=successful_full_sessions,
        )

    async def _execute_single_hook(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        """Execute a single hook for a session.

        Args:
            session: Full session+kernel data
            status: The status the session is transitioning to
        """
        hook = self._hook_registry.get_hook(status)
        if hook:
            await hook.execute(session)

    async def _broadcast_transition_events(
        self,
        sessions: list[SessionTransitionInfo],
        to_status: SessionStatus,
    ) -> None:
        """Broadcast scheduling events for session status transitions.

        Creates SchedulingBroadcastEvent for each session and broadcasts them in batch.
        Uses session data from SessionTransitionInfo (session_id, creation_id, reason).

        Args:
            sessions: Sessions that transitioned successfully
            to_status: The target status sessions transitioned to
        """
        if not sessions:
            return

        events: list[AbstractBroadcastEvent] = []
        for session_info in sessions:
            if session_info.creation_id is None:
                log.warning(
                    "Skipping event broadcast for session {} - missing creation_id",
                    session_info.session_id,
                )
                continue

            events.append(
                SchedulingBroadcastEvent(
                    session_id=session_info.session_id,
                    creation_id=session_info.creation_id,
                    status_transition=str(to_status),
                    reason=session_info.reason or "triggered-by-scheduler",
                )
            )

        if events:
            await self._event_producer.broadcast_events_batch(events)
            log.debug(
                "Broadcast {} transition events for status {}",
                len(events),
                to_status,
            )

    async def _handle_result(
        self,
        handler: SessionLifecycleHandler,
        result: SessionExecutionResult,
        records: Mapping[SessionId, ExecutionRecord],
        sessions: list[SessionWithKernels],
    ) -> FailureClassificationResult | None:
        """Apply status transitions using handler.status_transitions() (BEP-1030).

        Handler reports what happened (successes/failures/skipped), and Coordinator applies
        policy-based classification for failures to determine the outcome:
        - need_retry: Can retry (default for failures)
        - expired: Timeout exceeded
        - give_up: Max retries exceeded

        Skipped sessions are recorded in history without status change.

        Args:
            handler: The lifecycle handler that produced the result
            result: Execution result containing successes, failures, and skipped
            records: Mapping of session IDs to their execution records for sub_steps
            sessions: Original sessions with phase_attempts for failure classification

        Returns:
            FailureClassificationResult if there were failures, None otherwise.
            Used by caller for post-processing with correct target statuses.
        """
        transitions = handler.status_transitions()
        handler_name = handler.name()
        classified: FailureClassificationResult | None = None

        # Get DB time once for all operations in this result handling
        current_time = await self._repository.get_db_now()

        # SUCCESS transitions
        if transitions.success and result.successes:
            await self._apply_transition(
                handler_name,
                result.successes,
                transitions.success,
                SchedulingResult.SUCCESS,
                records,
                current_time,
            )
            # Broadcast events for successful transitions
            if transitions.success.session:
                await self._broadcast_transition_events(
                    result.successes, transitions.success.session
                )

        # FAILURE transitions - Coordinator classifies failures into give_up/expired/need_retry
        if result.failures:
            classified = self._classify_failures(result.failures, sessions, current_time)

            # Apply transitions for each classification
            if classified.give_up and transitions.give_up:
                await self._apply_transition(
                    handler_name,
                    classified.give_up,
                    transitions.give_up,
                    SchedulingResult.GIVE_UP,
                    records,
                    current_time,
                )

            if classified.expired and transitions.expired:
                await self._apply_transition(
                    handler_name,
                    classified.expired,
                    transitions.expired,
                    SchedulingResult.EXPIRED,
                    records,
                    current_time,
                )

            if classified.need_retry and transitions.need_retry:
                await self._apply_transition(
                    handler_name,
                    classified.need_retry,
                    transitions.need_retry,
                    SchedulingResult.NEED_RETRY,
                    records,
                    current_time,
                )

        # SKIPPED - Record history without status change
        if result.skipped:
            await self._record_skipped_history(handler_name, result.skipped, records)

        return classified

    def _classify_failures(
        self,
        failures: list[SessionTransitionInfo],
        sessions: list[SessionWithKernels],
        current_time: datetime,
    ) -> FailureClassificationResult:
        """Classify failures into give_up, expired, need_retry.

        Pure classification based on conditions only. The caller (_handle_result)
        decides whether to apply transitions based on handler's transition definitions.

        Classification priority (first match wins):
        1. give_up: phase_attempts >= SERVICE_MAX_RETRIES
        2. expired: timeout exceeded
        3. need_retry: default

        Args:
            failures: Failed session transition info
            sessions: Original sessions with phase_attempts and phase_started_at populated
            current_time: Current database time for timeout comparison

        Returns:
            FailureClassificationResult with give_up, expired, need_retry lists
        """
        session_map = {s.session_info.identity.id: s for s in sessions}

        give_up_failures: list[SessionTransitionInfo] = []
        expired_failures: list[SessionTransitionInfo] = []
        retry_failures: list[SessionTransitionInfo] = []

        for failure in failures:
            session = session_map.get(failure.session_id)
            if not session:
                # Session not found - skip (shouldn't happen)
                continue

            # 1. Check max retries exceeded → give_up
            if session.phase_attempts >= SERVICE_MAX_RETRIES:
                give_up_failures.append(failure)
                continue

            # 2. Check timeout exceeded → expired
            if session.phase_started_at:
                status = session.session_info.lifecycle.status
                timeout = STATUS_TIMEOUT_MAP.get(status)
                if timeout:
                    elapsed = (current_time - session.phase_started_at).total_seconds()
                    if elapsed > timeout:
                        expired_failures.append(failure)
                        continue

            # 3. Default → need_retry
            retry_failures.append(failure)

        return FailureClassificationResult(
            give_up=give_up_failures,
            expired=expired_failures,
            need_retry=retry_failures,
        )

    async def _apply_transition(
        self,
        handler_name: str,
        session_infos: list[Any],
        transition: TransitionStatus,
        scheduling_result: SchedulingResult,
        records: Mapping[SessionId, ExecutionRecord],
        status_changed_at: datetime,
    ) -> None:
        """Apply a single transition type to sessions (BEP-1030).

        Args:
            handler_name: Name of the handler for logging and history
            session_infos: List of SessionTransitionInfo for the sessions to update
            transition: Target status transition to apply
            scheduling_result: Result type for history recording
            records: Mapping of session IDs to their execution records
            status_changed_at: Database timestamp for status change
        """
        if not session_infos:
            return

        session_ids = [s.session_id for s in session_infos]

        # Session status update
        if transition.session:
            updater = BatchUpdater(
                spec=SessionStatusBatchUpdaterSpec(
                    to_status=transition.session,
                    status_changed_at=status_changed_at,
                ),
                conditions=[SessionConditions.by_ids(session_ids)],
            )
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=info.session_id,
                    phase=handler_name,
                    result=scheduling_result,
                    message=f"{handler_name} {scheduling_result.value.lower()}",
                    from_status=info.from_status,
                    to_status=transition.session,
                    error_code=info.error_code,
                    sub_steps=extract_sub_steps_for_entity(info.session_id, records),
                )
                for info in session_infos
            ]
            updated = await self._repository.update_with_history(
                updater, BulkCreator(specs=history_specs)
            )
            log.debug(
                "{}: Updated {} sessions to {} ({})",
                handler_name,
                updated,
                transition.session,
                scheduling_result.value,
            )

        # Kernel status reset if transitioning to PENDING
        if transition.kernel == KernelStatus.PENDING:
            await self._apply_kernel_pending_resets(handler_name, session_ids)

    async def _apply_kernel_pending_resets(
        self,
        handler_name: str,
        session_ids: list[SessionId],
    ) -> None:
        """Reset kernels to PENDING for sessions going back to PENDING.

        When sessions exceed max retries, they go back to PENDING for re-scheduling.
        This also resets their kernels to PENDING and clears agent assignments.

        Args:
            handler_name: Name of the handler for logging
            session_ids: List of session IDs whose kernels should be reset
        """
        if not session_ids:
            return

        reset_count = await self._kernel_state_engine.reset_kernels_to_pending_for_sessions(
            session_ids,
            reason="EXCEEDED_MAX_RETRIES",
        )
        log.debug(
            "{}: Reset {} kernels to PENDING for {} sessions",
            handler_name,
            reset_count,
            len(session_ids),
        )

    async def _record_skipped_history(
        self,
        handler_name: str,
        session_infos: list[SessionTransitionInfo],
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
        """Record history for skipped sessions without status change.

        Skipped sessions are those that were not processed due to being blocked
        by other sessions (e.g., scheduling attempt blocked by higher priority sessions).

        Args:
            handler_name: Name of the handler for history recording
            session_infos: List of skipped session information
            records: Mapping of session IDs to their execution records for sub_steps
        """
        if not session_infos:
            return

        history_specs = [
            SessionSchedulingHistoryCreatorSpec(
                session_id=info.session_id,
                phase=handler_name,
                result=SchedulingResult.SKIPPED,
                message=info.reason or f"{handler_name} skipped",
                from_status=info.from_status,
                to_status=info.from_status,  # No status change
                error_code=info.error_code,
                sub_steps=extract_sub_steps_for_entity(info.session_id, records),
            )
            for info in session_infos
        ]
        await self._repository.create_scheduling_history(BulkCreator(specs=history_specs))
        log.debug(
            "{}: Recorded {} skipped sessions in history",
            handler_name,
            len(session_infos),
        )

    def _collect_target_statuses(
        self,
        transitions: StatusTransitions,
        successes: list[SessionTransitionInfo],
        classified: FailureClassificationResult | None,
    ) -> set[SessionStatus]:
        """Collect all target statuses from successes and classified failures.

        Args:
            transitions: Status transitions defined by the handler
            successes: List of successful session transitions
            classified: Classified failures (give_up, expired, need_retry)

        Returns:
            Set of all target statuses that sessions transitioned to
        """
        target_statuses: set[SessionStatus] = set()

        # Add success target status
        if successes and transitions.success and transitions.success.session:
            target_statuses.add(transitions.success.session)

        # Add failure target statuses from classified failures
        if classified:
            if classified.give_up and transitions.give_up and transitions.give_up.session:
                target_statuses.add(transitions.give_up.session)
            if classified.expired and transitions.expired and transitions.expired.session:
                target_statuses.add(transitions.expired.session)
            if classified.need_retry and transitions.need_retry and transitions.need_retry.session:
                target_statuses.add(transitions.need_retry.session)

        return target_statuses

    async def _run_post_processors(
        self,
        result: SessionExecutionResult,
        target_statuses: set[SessionStatus],
    ) -> None:
        """Run all post-processors for session handlers in parallel.

        Args:
            result: Execution result containing successes and failures
            target_statuses: Set of target statuses sessions transitioned to
        """
        context = PostProcessorContext(result=result, target_statuses=target_statuses)
        results = await asyncio.gather(
            *[post_processor.execute(context) for post_processor in self._post_processors],
            return_exceptions=True,
        )
        for post_processor, res in zip(self._post_processors, results, strict=True):
            if isinstance(res, BaseException):
                log.warning(
                    "Post-processor {} failed: {}",
                    post_processor.__class__.__name__,
                    res,
                )

    async def _run_kernel_post_processors(
        self,
        result: KernelExecutionResult,
        target_statuses: set[KernelStatus],
    ) -> None:
        """Run all post-processors for kernel handlers in parallel.

        Args:
            result: Kernel execution result containing successes and failures
            target_statuses: Set of target kernel statuses that kernels transitioned to
        """
        context = KernelPostProcessorContext(result=result, target_statuses=target_statuses)
        results = await asyncio.gather(
            *[post_processor.execute(context) for post_processor in self._kernel_post_processors],
            return_exceptions=True,
        )
        for post_processor, res in zip(self._kernel_post_processors, results, strict=True):
            if isinstance(res, BaseException):
                log.warning(
                    "Kernel post-processor {} failed: {}",
                    post_processor.__class__.__name__,
                    res,
                )

    def _collect_kernel_target_statuses(
        self,
        transitions: KernelStatusTransitions,
        result: KernelExecutionResult,
    ) -> set[KernelStatus]:
        """Collect all target kernel statuses from successes and failures.

        Args:
            transitions: Kernel status transitions defined by the handler
            result: Kernel execution result

        Returns:
            Set of all target kernel statuses that kernels transitioned to
        """
        target_statuses: set[KernelStatus] = set()

        if result.successes and transitions.success:
            target_statuses.add(transitions.success)
        if result.failures and transitions.failure:
            target_statuses.add(transitions.failure)

        return target_statuses

    async def process_schedule(
        self,
        schedule_type: ScheduleType,
    ) -> bool:
        """
        Force processing of a specific schedule type.
        This method processes the scheduling operation even if it was not requested for guaranteed execution.
        So it should be called in long term loops.

        :param schedule_type: Type of scheduling operation
        :return: True if operation was performed, False otherwise
        """
        return await self.process_lifecycle_schedule(schedule_type)

    async def process_if_needed(self, schedule_type: ScheduleType) -> bool:
        """
        Process scheduling operation if needed (based on internal state).
        This method checks if the scheduling operation was requested and processes it if so.

        :param schedule_type: Type of scheduling operation
        :return: True if operation was performed, False otherwise
        """
        # Check internal state (uses Redis marks)
        if not await self._valkey_schedule.load_and_delete_schedule_mark(schedule_type.value):
            return False

        return await self.process_schedule(schedule_type)

    # Kernel event handling methods using the coordinator's kernel state engine

    async def handle_kernel_pulling(self, event: KernelPullingAnycastEvent) -> bool:
        """Handle kernel pulling event through the kernel state engine."""
        result = await self._kernel_state_engine.mark_kernel_pulling(event.kernel_id, event.reason)
        if result:
            # Request CHECK_PULLING_PROGRESS to monitor image pull progress
            await self._scheduling_controller.mark_scheduling_needed([
                ScheduleType.CHECK_PULLING_PROGRESS,
            ])
        return result

    async def handle_kernel_creating(self, event: KernelCreatingAnycastEvent) -> bool:
        """Handle kernel creating event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_creating(event.kernel_id, event.reason)

    async def handle_kernel_running(self, event: KernelStartedAnycastEvent) -> bool:
        """Handle kernel running event through the kernel state engine."""
        # Convert event data to dataclass (always present, may be empty)
        creation_info = KernelCreationInfo.from_dict(dict(event.creation_info))
        result = await self._kernel_state_engine.mark_kernel_running(
            event.kernel_id,
            event.reason,
            creation_info,
        )
        if result:
            # Request CHECK_CREATING_PROGRESS to check if session should transition to RUNNING
            await self._scheduling_controller.mark_scheduling_needed([
                ScheduleType.CHECK_CREATING_PROGRESS,
            ])
        return result

    async def handle_kernel_preparing(self, event: KernelPreparingAnycastEvent) -> bool:
        """Handle kernel preparing event through the kernel state engine."""
        result = await self._kernel_state_engine.mark_kernel_preparing(event.kernel_id)
        if result:
            # Request CHECK_PRECONDITION to check if images are ready
            await self._scheduling_controller.mark_scheduling_needed([
                ScheduleType.CHECK_PRECONDITION,
            ])
        return result

    async def handle_kernel_cancelled(self, event: KernelCancelledAnycastEvent) -> bool:
        """Handle kernel cancelled event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_cancelled(
            event.kernel_id, event.session_id, event.reason
        )

    async def handle_kernel_terminated(self, event: KernelTerminatedAnycastEvent) -> bool:
        """Handle kernel terminated event through the kernel state engine."""
        log.info("Handling termination of kernel {}", event.kernel_id)
        result = await self._kernel_state_engine.mark_kernel_terminated(
            event.kernel_id, event.reason, event.exit_code
        )
        if result:
            # Request DETECT_KERNEL_TERMINATION and CHECK_TERMINATING_PROGRESS
            await self._scheduling_controller.mark_scheduling_needed([
                ScheduleType.DETECT_KERNEL_TERMINATION,
                ScheduleType.CHECK_TERMINATING_PROGRESS,
            ])
        return result

    # Image-related kernel state update methods

    async def update_kernels_to_pulling_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: str | None = None,
    ) -> None:
        """Update kernel status from PREPARING to PULLING for the specified image on an agent."""
        await self._kernel_state_engine.update_kernels_to_pulling_for_image(
            agent_id, image, image_ref
        )

    async def update_kernels_to_prepared_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: str | None = None,
    ) -> None:
        """Update kernel status to PREPARED for the specified image on an agent."""
        result = await self._kernel_state_engine.update_kernels_to_prepared_for_image(
            agent_id, image, image_ref
        )
        if result > 0:
            log.info(
                "Updated {} kernels to PREPARED state for agent:{} image:{}",
                result,
                agent_id,
                image,
            )
            # Request scheduling to check if sessions can transition to RUNNING
            await self._scheduling_controller.mark_scheduling_needed([
                ScheduleType.CHECK_PULLING_PROGRESS,
            ])

    async def cancel_kernels_for_failed_image(
        self,
        agent_id: AgentId,
        image: str,
        error_msg: str,
        image_ref: str | None = None,
    ) -> None:
        """Cancel kernels for an image that failed to be available on an agent."""
        await self._kernel_state_engine.cancel_kernels_for_failed_image(
            agent_id, image, error_msg, image_ref
        )
        # No need to request scheduling for cancelled kernels

    @staticmethod
    def _create_task_specs() -> list[SchedulerTaskSpec]:
        """Create task specifications for all schedule types."""
        return [
            # Regular scheduling operations with both short and long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.SCHEDULE,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_PRECONDITION,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.START,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.TERMINATE,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Sweep is a maintenance task - only needs long cycle task
            SchedulerTaskSpec(
                ScheduleType.SWEEP,
                short_interval=None,  # No short-cycle task for maintenance
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Sweep stale kernels - maintenance task to clean up kernels with stale presence
            SchedulerTaskSpec(
                ScheduleType.SWEEP_STALE_KERNELS,
                short_interval=None,  # No short-cycle task for maintenance
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Progress check operations with both short and long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.CHECK_PULLING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_CREATING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_TERMINATING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Detect active sessions with any kernel TERMINATED/CANCELLED
            SchedulerTaskSpec(
                ScheduleType.DETECT_KERNEL_TERMINATION,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Fair share observation - records RUNNING kernel usage for fair share calculation
            SchedulerTaskSpec(
                ScheduleType.OBSERVE_FAIR_SHARE,
                short_interval=None,  # No short-cycle task for observation
                long_interval=300.0,  # 5 minutes
                initial_delay=60.0,  # Start 1 minute after manager starts
            ),
        ]

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for leader-based scheduling."""
        timer_specs = self._create_task_specs()
        specs: list[EventTaskSpec] = []

        for spec in timer_specs:
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
