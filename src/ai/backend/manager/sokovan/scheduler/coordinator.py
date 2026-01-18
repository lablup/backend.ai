import asyncio
import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Optional

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
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.common.types import AgentId, SessionId, SessionTypes
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    TransitionStatus,
)
from ai.backend.manager.metrics.scheduler import SchedulerOperationMetricObserver
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.pagination import NoPagination
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.scheduler.updaters import SessionStatusBatchUpdaterSpec
from ai.backend.manager.repositories.scheduling_history.creators import (
    SessionSchedulingHistoryCreatorSpec,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.sokovan.scheduler.scheduler import SchedulerComponents
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import DistributedLockFactory

from .handlers import (
    CheckPreconditionLifecycleHandler,
    DetectTerminationPromotionHandler,
    PromoteToPreparedPromotionHandler,
    PromoteToRunningPromotionHandler,
    PromoteToTerminatedPromotionHandler,
    RetryCreatingLifecycleHandler,
    RetryPreparingLifecycleHandler,
    ScheduleSessionsLifecycleHandler,
    SessionLifecycleHandler,
    SessionPromotionHandler,
    StartSessionsLifecycleHandler,
    SweepLostAgentKernelsLifecycleHandler,
    SweepSessionsLifecycleHandler,
    SweepStaleKernelsLifecycleHandler,
    TerminateSessionsLifecycleHandler,
)
from .hooks.base import AbstractSessionHook
from .hooks.registry import HookRegistry
from .kernel import KernelStateEngine
from .recorder import SessionRecorderContext
from .results import SessionExecutionResult, SessionTransitionInfo
from .types import KernelCreationInfo, KernelTerminationInfo, SessionWithKernels

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class SchedulerTaskSpec:
    """Specification for a scheduler's periodic task."""

    schedule_type: ScheduleType
    short_interval: Optional[float] = None  # None means no short-cycle task
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


@dataclass(frozen=True)
class TransitionHookConfig:
    """Configuration for hooks triggered on session status transitions.

    Used by Coordinator to execute hooks when sessions transition to specific statuses.
    Hooks are executed after handler logic but before status transition is applied.
    """

    blocking: bool
    """If True, hook failure prevents the session from transitioning.
    If False, hook is best-effort - failures are logged but transition proceeds."""


class ScheduleCoordinator:
    """
    Coordinate scheduling operations based on scheduling needs.
    Handles the actual scheduling logic and state management.
    """

    _valkey_schedule: ValkeyScheduleClient
    _components: SchedulerComponents
    _scheduling_controller: SchedulingController
    _repository: SchedulerRepository
    _lifecycle_handlers: Mapping[ScheduleType, SessionLifecycleHandler]
    _promotion_handlers: Mapping[ScheduleType, SessionPromotionHandler]
    _operation_metrics: SchedulerOperationMetricObserver
    _kernel_state_engine: KernelStateEngine
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer
    _hook_registry: HookRegistry
    _transition_hooks: Mapping[SessionStatus, TransitionHookConfig]

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        components: SchedulerComponents,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
    ) -> None:
        self._valkey_schedule = valkey_schedule
        self._components = components
        self._scheduling_controller = scheduling_controller
        self._repository = components.repository
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = components.config_provider
        self._operation_metrics = SchedulerOperationMetricObserver.instance()

        # Initialize kernel state engine with the component's repository
        self._kernel_state_engine = KernelStateEngine(components.repository)

        # Initialize hook registry and transition hooks
        self._hook_registry = components.hook_registry
        self._transition_hooks = self._init_transition_hooks()

        # Initialize lifecycle handlers
        self._lifecycle_handlers = self._init_lifecycle_handlers()

        # Initialize promotion handlers
        self._promotion_handlers = self._init_promotion_handlers()

    def _init_transition_hooks(self) -> Mapping[SessionStatus, TransitionHookConfig]:
        """Initialize mapping of target statuses to their hook configurations.

        Hooks are executed when sessions transition to specific statuses:
        - RUNNING: blocking hook (failure prevents transition)
        - TERMINATED: best-effort hook (failure logged but transition proceeds)
        """
        return {
            SessionStatus.RUNNING: TransitionHookConfig(blocking=True),
            SessionStatus.TERMINATED: TransitionHookConfig(blocking=False),
        }

    def _init_lifecycle_handlers(self) -> Mapping[ScheduleType, SessionLifecycleHandler]:
        """Initialize and return the mapping of schedule types to their lifecycle handlers.

        Lifecycle handlers follow the DeploymentCoordinator pattern where:
        - Coordinator queries sessions based on handler's target_statuses()
        - Coordinator iterates over scaling groups
        - Handler executes business logic and returns successes/failures/stales
        - Coordinator applies status transitions based on handler's declared statuses

        Note: Promotion handlers (CHECK_*_PROGRESS, CHECK_RUNNING_SESSION_TERMINATION)
        are now in _init_promotion_handlers() using SessionPromotionHandler interface.
        Legacy progress handlers are kept here for backward compatibility during migration.
        """
        # Get components for handlers that need them
        launcher = self._components.launcher
        terminator = self._components.terminator
        provisioner = self._components.provisioner

        return {
            # Lifecycle handlers
            ScheduleType.SCHEDULE: ScheduleSessionsLifecycleHandler(
                provisioner,
                self._scheduling_controller,
                self._event_producer,
                self._repository,
            ),
            ScheduleType.CHECK_PRECONDITION: CheckPreconditionLifecycleHandler(
                launcher,
                self._repository,
                self._scheduling_controller,
                self._event_producer,
            ),
            ScheduleType.START: StartSessionsLifecycleHandler(
                launcher,
                self._repository,
                self._event_producer,
            ),
            ScheduleType.TERMINATE: TerminateSessionsLifecycleHandler(
                terminator,
                self._repository,
            ),
            # Recovery handlers
            ScheduleType.RETRY_PREPARING: RetryPreparingLifecycleHandler(
                launcher,
                self._repository,
            ),
            ScheduleType.RETRY_CREATING: RetryCreatingLifecycleHandler(
                launcher,
                self._repository,
            ),
            # Maintenance handlers
            ScheduleType.SWEEP: SweepSessionsLifecycleHandler(
                self._repository,
            ),
            ScheduleType.SWEEP_LOST_AGENT_KERNELS: SweepLostAgentKernelsLifecycleHandler(
                terminator,
                self._repository,
            ),
            ScheduleType.SWEEP_STALE_KERNELS: SweepStaleKernelsLifecycleHandler(
                terminator,
                self._valkey_schedule,
                self._repository,
            ),
        }

    def _init_promotion_handlers(self) -> Mapping[ScheduleType, SessionPromotionHandler]:
        """Initialize and return the mapping of schedule types to their promotion handlers.

        Promotion handlers check kernel status conditions (ALL/ANY/NOT_ANY) to
        determine if sessions should be promoted to a new status.
        """
        return {
            ScheduleType.CHECK_PULLING_PROGRESS: PromoteToPreparedPromotionHandler(
                self._event_producer,
            ),
            ScheduleType.CHECK_CREATING_PROGRESS: PromoteToRunningPromotionHandler(
                self._scheduling_controller,
                self._event_producer,
                self._repository,
            ),
            ScheduleType.CHECK_TERMINATING_PROGRESS: PromoteToTerminatedPromotionHandler(
                self._scheduling_controller,
                self._event_producer,
                self._repository,
            ),
            ScheduleType.CHECK_RUNNING_SESSION_TERMINATION: DetectTerminationPromotionHandler(
                self._valkey_schedule,
                self._repository,
            ),
        }

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
        # Check promotion handlers first, then lifecycle handlers
        promotion_handler = self._promotion_handlers.get(schedule_type)
        if promotion_handler:
            return await self._process_promotion_schedule(schedule_type, promotion_handler)

        lifecycle_handler = self._lifecycle_handlers.get(schedule_type)
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
        handler: SessionPromotionHandler,
    ) -> bool:
        """Process a promotion handler schedule type.

        Promotion handlers use ALL/ANY/NOT_ANY kernel status conditions,
        so they use get_sessions_for_promotion() instead of get_sessions_for_handler().
        """
        try:
            log.debug("Processing promotion schedule type: {}", schedule_type.value)

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
                        self._process_promotion_scaling_group(handler, schedule_type, scaling_group)
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

        # Create recorder scoped to this scaling group
        recorder_scope = f"{schedule_type.value}:{scaling_group}"
        with SessionRecorderContext.scope(recorder_scope, entity_ids=session_ids) as pool:
            # Execute handler logic
            result = await handler.execute(scaling_group, sessions)

            # Get recorded steps for history
            all_records = pool.build_all_records()

            # Apply status transitions immediately for this scaling group (BEP-1030)
            await self._handle_result(handler, result, all_records)

            # Emit metrics per scaling group
            self._operation_metrics.observe_success(
                operation=handler.name(),
                count=result.success_count(),
            )

            # Post-process if needed (per scaling group)
            if result.needs_post_processing():
                try:
                    await handler.post_process(result)
                except Exception as e:
                    log.error(
                        "Error during post-processing for scaling group {}: {}",
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
        handler: SessionPromotionHandler,
        schedule_type: ScheduleType,
        scaling_group: str,
    ) -> None:
        """Process a single scaling group for the given promotion handler.

        This method handles all processing for one scaling group using
        promotion handler semantics (ALL/ANY/NOT_ANY kernel matching).

        Args:
            handler: The promotion handler to execute
            schedule_type: Type of scheduling operation
            scaling_group: The scaling group to process
        """
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                SessionConditions.by_scaling_group(scaling_group),
                SessionConditions.by_statuses(handler.target_statuses()),
                SessionConditions.by_kernel_match(
                    handler.target_kernel_statuses(),
                    handler.kernel_match_type(),
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
            # Execute handler logic (handlers receive SessionInfo directly)
            result = await handler.execute(scaling_group, session_infos)

            # Get recorded steps for history
            all_records = pool.build_all_records()

            # Apply status transitions immediately for this scaling group
            await self._handle_promotion_status_transitions(handler, result, all_records)

            # Emit metrics per scaling group
            self._operation_metrics.observe_success(
                operation=handler.name(),
                count=result.success_count(),
            )

            # Post-process if needed (per scaling group)
            if result.needs_post_processing():
                try:
                    await handler.post_process(result)
                except Exception as e:
                    log.error(
                        "Error during post-processing for scaling group {}: {}",
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
        handler: SessionPromotionHandler,
        result: SessionExecutionResult,
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
        """Apply status transitions for promotion handler execution results (BEP-1030).

        Promotion handlers only change session status (not kernel status).
        Kernel status changes are driven by agent events, not coordinator.

        Hook execution is centralized here:
        1. Check if target status has hooks configured
        2. If hooks exist, fetch full session data and execute hooks
        3. For blocking hooks, filter out sessions where hooks failed
        4. Apply sessions_running_data update for hook-success sessions (if present)
        5. Apply status transition for remaining sessions

        Args:
            handler: The promotion handler that produced the result
            result: Execution result containing successes and sessions_running_data
            records: Mapping of session IDs to their execution records for sub_steps
        """
        transitions = handler.status_transitions()
        handler_name = handler.name()

        if not transitions.success or not result.successes:
            return

        to_status = transitions.success
        sessions_to_transition = result.successes

        # Execute hooks if configured for this status
        hook_config = self._transition_hooks.get(to_status)
        if hook_config:
            sessions_to_transition = await self._execute_transition_hooks(
                sessions_to_transition,
                to_status,
                hook_config,
            )

        # Apply status transition for sessions that passed hooks
        if sessions_to_transition:
            # Filter sessions_running_data to only include sessions that passed hooks
            successful_session_ids = {s.session_id for s in sessions_to_transition}
            if result.sessions_running_data:
                filtered_running_data = [
                    data
                    for data in result.sessions_running_data
                    if data.session_id in successful_session_ids
                ]
                if filtered_running_data:
                    await self._repository.update_sessions_to_running(filtered_running_data)

            # Create TransitionStatus with kernel=None (promotion doesn't change kernel status)
            transition = TransitionStatus(session=to_status, kernel=None)
            await self._apply_transition(
                handler_name,
                sessions_to_transition,
                transition,
                SchedulingResult.SUCCESS,
                records,
            )

    async def _execute_transition_hooks(
        self,
        session_infos: list[SessionTransitionInfo],
        target_status: SessionStatus,
        hook_config: TransitionHookConfig,
    ) -> list[SessionTransitionInfo]:
        """Execute transition hooks for sessions moving to target_status.

        Fetches full session+kernel data, executes hooks per session type,
        and returns sessions that should proceed with the transition.

        Args:
            session_infos: Sessions to execute hooks for
            target_status: The status sessions are transitioning to
            hook_config: Hook configuration (blocking behavior)

        Returns:
            For blocking hooks: Only sessions where hook succeeded
            For best-effort hooks: All sessions (failures are logged)
        """
        if not session_infos:
            return []

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
            return []

        # Build session_id -> SessionTransitionInfo mapping for results
        info_map = {s.session_id: s for s in session_infos}

        # Execute hooks concurrently
        hook_coroutines = [
            self._execute_single_hook(session, target_status)
            for session in full_sessions
        ]
        hook_results = await asyncio.gather(*hook_coroutines, return_exceptions=True)

        # Process results based on blocking behavior
        successful_sessions: list[SessionTransitionInfo] = []
        for session, hook_result in zip(full_sessions, hook_results, strict=True):
            session_id = session.session_info.identity.id
            original_info = info_map.get(session_id)

            if original_info is None:
                continue

            if isinstance(hook_result, BaseException):
                log.error(
                    "Hook on_transition to {} failed for session {}: {}",
                    target_status,
                    session_id,
                    hook_result,
                )
                if hook_config.blocking:
                    # Blocking hook failed - don't include in successful sessions
                    continue
                # Best-effort hook failed - still include in successful sessions

            successful_sessions.append(original_info)

        log.info(
            "Executed on_transition hooks for {} sessions transitioning to {} ({} succeeded)",
            len(full_sessions),
            target_status,
            len(successful_sessions),
        )

        return successful_sessions

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
        session_type = session.session_info.metadata.session_type
        hook = self._hook_registry.get_hook(session_type)
        await hook.on_transition(session, status)

    async def _handle_result(
        self,
        handler: SessionLifecycleHandler,
        result: SessionExecutionResult,
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
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
        """
        transitions = handler.status_transitions()
        handler_name = handler.name()

        # SUCCESS transitions
        if transitions.success and result.successes:
            await self._apply_transition(
                handler_name,
                result.successes,
                transitions.success,
                SchedulingResult.SUCCESS,
                records,
            )

        # FAILURE transitions - Coordinator classifies failures into need_retry/expired/give_up
        # TODO: Implement policy-based classification in Phase 4:
        #   - Check timeout threshold → expired
        #   - Check retry count vs max retries → give_up
        #   - Otherwise → need_retry
        # For now, use the first defined transition in handler's status_transitions()
        if result.failures:
            if transitions.need_retry:
                await self._apply_transition(
                    handler_name,
                    result.failures,
                    transitions.need_retry,
                    SchedulingResult.NEED_RETRY,
                    records,
                )
            elif transitions.expired:
                # Use expired if need_retry is not defined (e.g., sweep handlers)
                await self._apply_transition(
                    handler_name,
                    result.failures,
                    transitions.expired,
                    SchedulingResult.EXPIRED,
                    records,
                )
            elif transitions.give_up:
                # Fallback to give_up
                await self._apply_transition(
                    handler_name,
                    result.failures,
                    transitions.give_up,
                    SchedulingResult.GIVE_UP,
                    records,
                )

        # SKIPPED - Record history without status change
        if result.skipped:
            await self._record_skipped_history(handler_name, result.skipped, records)

        # Apply kernel terminations (processed together with session status changes)
        if result.kernel_terminations:
            await self._apply_kernel_terminations(handler_name, result.kernel_terminations)

    async def _apply_transition(
        self,
        handler_name: str,
        session_infos: list,
        transition: TransitionStatus,
        scheduling_result: SchedulingResult,
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
        """Apply a single transition type to sessions (BEP-1030).

        Args:
            handler_name: Name of the handler for logging and history
            session_infos: List of SessionTransitionInfo for the sessions to update
            transition: Target status transition to apply
            scheduling_result: Result type for history recording
            records: Mapping of session IDs to their execution records
        """
        if not session_infos:
            return

        session_ids = [s.session_id for s in session_infos]

        # Session status update
        if transition.session:
            updater = BatchUpdater(
                spec=SessionStatusBatchUpdaterSpec(to_status=transition.session),
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

    async def _apply_kernel_terminations(
        self,
        handler_name: str,
        kernel_terminations: list[KernelTerminationInfo],
    ) -> None:
        """Apply kernel terminations using the kernel state engine.

        This is processed together with session status changes to ensure
        consistency in the coordinator.

        Args:
            handler_name: Name of the handler for logging
            kernel_terminations: List of kernel terminations to apply
        """
        for termination in kernel_terminations:
            await self._kernel_state_engine.mark_kernel_terminated(
                termination.kernel_id,
                termination.reason,
            )
        if kernel_terminations:
            log.debug(
                "{}: Terminated {} kernels",
                handler_name,
                len(kernel_terminations),
            )

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
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_PULLING_PROGRESS
            )
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
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_CREATING_PROGRESS
            )
        return result

    async def handle_kernel_preparing(self, event: KernelPreparingAnycastEvent) -> bool:
        """Handle kernel preparing event through the kernel state engine."""
        result = await self._kernel_state_engine.mark_kernel_preparing(event.kernel_id)
        if result:
            # Request CHECK_PRECONDITION to check if images are ready
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_PRECONDITION
            )
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
            # Request CHECK_RUNNING_SESSION_TERMINATION to check if RUNNING session should become TERMINATING
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_RUNNING_SESSION_TERMINATION
            )
            # Request CHECK_TERMINATING_PROGRESS to check if session should transition to TERMINATED
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_TERMINATING_PROGRESS
            )
        return result

    # Image-related kernel state update methods

    async def update_kernels_to_pulling_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: Optional[str] = None,
    ) -> None:
        """Update kernel status from PREPARING to PULLING for the specified image on an agent."""
        await self._kernel_state_engine.update_kernels_to_pulling_for_image(
            agent_id, image, image_ref
        )

    async def update_kernels_to_prepared_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: Optional[str] = None,
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
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_PULLING_PROGRESS,
            )

    async def cancel_kernels_for_failed_image(
        self,
        agent_id: AgentId,
        image: str,
        error_msg: str,
        image_ref: Optional[str] = None,
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
            # Sweep lost agent kernels - maintenance task to clean up kernels with lost agents
            SchedulerTaskSpec(
                ScheduleType.SWEEP_LOST_AGENT_KERNELS,
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
            # Check RUNNING sessions where all kernels are TERMINATED
            SchedulerTaskSpec(
                ScheduleType.CHECK_RUNNING_SESSION_TERMINATION,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Retry operations - only long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.RETRY_PREPARING,
                short_interval=None,  # No short-cycle task
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
            ),
            SchedulerTaskSpec(
                ScheduleType.RETRY_CREATING,
                short_interval=None,  # No short-cycle task
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
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
