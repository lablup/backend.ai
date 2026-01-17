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
from ai.backend.common.types import AgentId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.metrics.scheduler import SchedulerOperationMetricObserver
from ai.backend.manager.repositories.base.creator import BulkCreator
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
    CheckCreatingProgressLifecycleHandler,
    CheckPreconditionLifecycleHandler,
    CheckPullingProgressLifecycleHandler,
    CheckRunningSessionTerminationLifecycleHandler,
    CheckTerminatingProgressLifecycleHandler,
    RetryCreatingLifecycleHandler,
    RetryPreparingLifecycleHandler,
    ScheduleSessionsLifecycleHandler,
    SessionLifecycleHandler,
    StartSessionsLifecycleHandler,
    SweepLostAgentKernelsLifecycleHandler,
    SweepSessionsLifecycleHandler,
    SweepStaleKernelsLifecycleHandler,
    TerminateSessionsLifecycleHandler,
)
from .kernel import KernelStateEngine
from .recorder import SessionRecorderContext
from .results import SessionExecutionResult
from .types import KernelCreationInfo, KernelTerminationInfo

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
    _operation_metrics: SchedulerOperationMetricObserver
    _kernel_state_engine: KernelStateEngine
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

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

        # Initialize lifecycle handlers
        self._lifecycle_handlers = self._init_lifecycle_handlers()

    def _init_lifecycle_handlers(self) -> Mapping[ScheduleType, SessionLifecycleHandler]:
        """Initialize and return the mapping of schedule types to their lifecycle handlers.

        Lifecycle handlers follow the DeploymentCoordinator pattern where:
        - Coordinator queries sessions based on handler's target_statuses()
        - Coordinator iterates over scaling groups
        - Handler executes business logic and returns successes/failures/stales
        - Coordinator applies status transitions based on handler's declared statuses
        """
        # Get components for handlers that need them
        hook_registry = self._components.hook_registry
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
            ScheduleType.CHECK_PULLING_PROGRESS: CheckPullingProgressLifecycleHandler(
                self._event_producer,
            ),
            ScheduleType.START: StartSessionsLifecycleHandler(
                launcher,
                self._repository,
                self._event_producer,
            ),
            ScheduleType.CHECK_CREATING_PROGRESS: CheckCreatingProgressLifecycleHandler(
                self._scheduling_controller,
                self._event_producer,
                self._repository,
                hook_registry,
            ),
            ScheduleType.TERMINATE: TerminateSessionsLifecycleHandler(
                terminator,
                self._repository,
            ),
            ScheduleType.CHECK_TERMINATING_PROGRESS: CheckTerminatingProgressLifecycleHandler(
                self._scheduling_controller,
                self._event_producer,
                self._repository,
                hook_registry,
            ),
            ScheduleType.CHECK_RUNNING_SESSION_TERMINATION: (
                CheckRunningSessionTerminationLifecycleHandler(
                    self._valkey_schedule,
                    self._repository,
                )
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
        handler = self._lifecycle_handlers.get(schedule_type)
        if not handler:
            log.warning("No lifecycle handler for schedule type: {}", schedule_type.value)
            return False

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

            # Apply status transitions immediately for this scaling group
            await self._handle_status_transitions(handler, result, all_records)

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

    async def _handle_status_transitions(
        self,
        handler: SessionLifecycleHandler,
        result: SessionExecutionResult,
        records: Mapping[SessionId, ExecutionRecord],
    ) -> None:
        """Apply status transitions based on handler execution results.

        Args:
            handler: The lifecycle handler that produced the result
            result: Execution result containing successes, failures, and stales
            records: Mapping of session IDs to their execution records for sub_steps
        """
        target_statuses = handler.target_statuses()
        handler_name = handler.name()

        # Update successful sessions
        success_status = handler.success_status()
        if success_status is not None and result.successes:
            updater = BatchUpdater(
                spec=SessionStatusBatchUpdaterSpec(to_status=success_status),
                conditions=[
                    SessionConditions.by_ids(result.success_ids()),
                    SessionConditions.by_statuses(target_statuses),
                ],
            )
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=s.session_id,
                    phase=handler_name,
                    result=SchedulingResult.SUCCESS,
                    message=f"{handler_name} completed successfully",
                    from_status=s.from_status,
                    to_status=success_status,
                    sub_steps=extract_sub_steps_for_entity(s.session_id, records),
                )
                for s in result.successes
            ]
            updated = await self._repository.update_with_history(
                updater, BulkCreator(specs=history_specs)
            )
            log.debug(
                "{}: Updated {} sessions to {} (success)",
                handler_name,
                updated,
                success_status,
            )

        # Update failed sessions
        failure_status = handler.failure_status()
        if failure_status is not None and result.failures:
            updater = BatchUpdater(
                spec=SessionStatusBatchUpdaterSpec(to_status=failure_status),
                conditions=[
                    SessionConditions.by_ids(result.failure_ids()),
                    SessionConditions.by_statuses(target_statuses),
                ],
            )
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=f.session_id,
                    phase=handler_name,
                    result=SchedulingResult.FAILURE,
                    message=f.reason,
                    from_status=f.from_status,
                    to_status=failure_status,
                    error_code=f.error_detail,
                    sub_steps=extract_sub_steps_for_entity(f.session_id, records),
                )
                for f in result.failures
            ]
            updated = await self._repository.update_with_history(
                updater, BulkCreator(specs=history_specs)
            )
            log.debug(
                "{}: Updated {} sessions to {} (failure)",
                handler_name,
                updated,
                failure_status,
            )

        # Update stale sessions
        stale_status = handler.stale_status()
        if stale_status is not None and result.stales:
            updater = BatchUpdater(
                spec=SessionStatusBatchUpdaterSpec(to_status=stale_status),
                conditions=[
                    SessionConditions.by_ids(result.stale_ids()),
                    SessionConditions.by_statuses(target_statuses),
                ],
            )
            history_specs = [
                SessionSchedulingHistoryCreatorSpec(
                    session_id=s.session_id,
                    phase=handler_name,
                    result=SchedulingResult.STALE,
                    message=f"{handler_name} marked as stale",
                    from_status=s.from_status,
                    to_status=stale_status,
                    sub_steps=extract_sub_steps_for_entity(s.session_id, records),
                )
                for s in result.stales
            ]
            updated = await self._repository.update_with_history(
                updater, BulkCreator(specs=history_specs)
            )
            log.debug(
                "{}: Updated {} sessions to {} (stale)",
                handler_name,
                updated,
                stale_status,
            )

            # When sessions go to PENDING, also reset their kernels
            if stale_status == SessionStatus.PENDING:
                stale_session_ids = result.stale_ids()
                await self._apply_kernel_pending_resets(handler_name, stale_session_ids)

        # Apply kernel terminations (processed together with session status changes)
        if result.kernel_terminations:
            await self._apply_kernel_terminations(handler_name, result.kernel_terminations)

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
