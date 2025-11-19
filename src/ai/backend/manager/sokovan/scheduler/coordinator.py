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
    KernelHeartbeatEvent,
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
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.metrics.scheduler import SchedulerOperationMetricObserver
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import DistributedLockFactory

from .handlers import (
    CheckCreatingProgressHandler,
    CheckPreconditionHandler,
    CheckPullingProgressHandler,
    CheckTerminatingProgressHandler,
    RetryCreatingHandler,
    RetryPreparingHandler,
    SchedulerHandler,
    ScheduleSessionsHandler,
    StartSessionsHandler,
    SweepLostAgentKernelsHandler,
    SweepSessionsHandler,
    TerminateSessionsHandler,
)
from .kernel import KernelStateEngine
from .types import KernelCreationInfo

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
    _scheduler: Scheduler
    _scheduling_controller: SchedulingController
    _schedule_handlers: Mapping[ScheduleType, SchedulerHandler]
    _operation_metrics: SchedulerOperationMetricObserver
    _kernel_state_engine: KernelStateEngine
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._valkey_schedule = valkey_schedule
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = config_provider
        self._operation_metrics = SchedulerOperationMetricObserver.instance()

        # Initialize kernel state engine with the scheduler's repository
        self._kernel_state_engine = KernelStateEngine(scheduler._repository)

        # Initialize handlers using a dedicated method
        self._schedule_handlers = self._init_handlers()

    def _init_handlers(self) -> Mapping[ScheduleType, SchedulerHandler]:
        """Initialize and return the mapping of schedule types to their handlers."""
        return {
            ScheduleType.SCHEDULE: ScheduleSessionsHandler(
                self._scheduler,
                self._scheduling_controller,
                self._event_producer,
                self._scheduler._repository,
            ),
            ScheduleType.CHECK_PRECONDITION: CheckPreconditionHandler(
                self._scheduler, self._scheduling_controller, self._event_producer
            ),
            ScheduleType.START: StartSessionsHandler(self._scheduler, self._event_producer),
            ScheduleType.TERMINATE: TerminateSessionsHandler(
                self._scheduler,
                self._scheduling_controller,
                self._event_producer,
                self._scheduler._repository,
            ),
            ScheduleType.SWEEP: SweepSessionsHandler(self._scheduler, self._scheduler._repository),
            ScheduleType.SWEEP_LOST_AGENT_KERNELS: SweepLostAgentKernelsHandler(
                self._scheduler, self._scheduler._repository
            ),
            ScheduleType.CHECK_PULLING_PROGRESS: CheckPullingProgressHandler(
                self._scheduler, self._scheduling_controller, self._event_producer
            ),
            ScheduleType.CHECK_CREATING_PROGRESS: CheckCreatingProgressHandler(
                self._scheduler, self._scheduling_controller, self._event_producer
            ),
            ScheduleType.CHECK_TERMINATING_PROGRESS: CheckTerminatingProgressHandler(
                self._scheduler,
                self._scheduling_controller,
                self._event_producer,
                self._scheduler._repository,
            ),
            ScheduleType.RETRY_PREPARING: RetryPreparingHandler(
                self._scheduler, self._scheduling_controller, self._event_producer
            ),
            ScheduleType.RETRY_CREATING: RetryCreatingHandler(
                self._scheduler, self._scheduling_controller, self._event_producer
            ),
        }

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
        try:
            log.debug("Processing schedule type: {}", schedule_type.value)

            # Get handler from map and execute
            handler = self._schedule_handlers.get(schedule_type)
            if not handler:
                log.warning("No handler for schedule type: {}", schedule_type.value)
                return False

            # Execute the handler with optional locking
            async with AsyncExitStack() as stack:
                stack.enter_context(self._operation_metrics.measure_operation(handler.name()))
                if handler.lock_id is not None:
                    lock_lifetime = (
                        self._config_provider.config.manager.session_schedule_lock_lifetime
                    )
                    await stack.enter_async_context(
                        self._lock_factory(handler.lock_id, lock_lifetime)
                    )
                result = await handler.execute()
                self._operation_metrics.observe_success(
                    operation=handler.name(), count=result.success_count()
                )
                if result.needs_post_processing():
                    try:
                        await handler.post_process(result)
                    except Exception as e:
                        log.error("Error during post-processing: {}", e)
            return True
        except Exception as e:
            log.exception(
                "Error processing schedule type {}: {}",
                schedule_type.value,
                e,
            )
            raise

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
        result = await self._kernel_state_engine.mark_kernel_terminated(
            event.kernel_id, event.reason, event.exit_code
        )
        if result:
            # Request CHECK_TERMINATING_PROGRESS to check if session should transition to TERMINATED
            await self._scheduling_controller.mark_scheduling_needed(
                ScheduleType.CHECK_TERMINATING_PROGRESS
            )
        return result

    async def handle_kernel_heartbeat(self, event: KernelHeartbeatEvent) -> bool:
        """Handle kernel heartbeat event through the kernel state engine."""
        return await self._kernel_state_engine.update_kernel_heartbeat(event.kernel_id)

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
