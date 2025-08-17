import logging

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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.metrics.scheduler import SchedulerOperationMetricObserver
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .handlers import (
    CheckCreatingProgressHandler,
    CheckPreconditionHandler,
    CheckPullingProgressHandler,
    CheckTerminatingProgressHandler,
    ScheduleHandler,
    ScheduleSessionsHandler,
    StartSessionsHandler,
    SweepSessionsHandler,
    TerminateSessionsHandler,
)
from .kernel import KernelStateEngine

log = BraceStyleAdapter(logging.getLogger(__name__))


class ScheduleCoordinator:
    """
    Coordinate scheduling operations based on scheduling needs.
    Handles the actual scheduling logic and state management.
    """

    _valkey_schedule: ValkeyScheduleClient
    _scheduler: "Scheduler"
    _scheduling_controller: SchedulingController
    _event_producer: EventProducer
    _schedule_handlers: dict[ScheduleType, ScheduleHandler]
    _scheduler_dispatcher: SchedulerDispatcher
    _operation_metrics: SchedulerOperationMetricObserver
    _kernel_state_engine: KernelStateEngine

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        scheduler: "Scheduler",
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        scheduler_dispatcher: SchedulerDispatcher,
    ) -> None:
        self._valkey_schedule = valkey_schedule
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._scheduler_dispatcher = scheduler_dispatcher
        self._operation_metrics = SchedulerOperationMetricObserver.instance()

        # Initialize kernel state engine with the scheduler's repository
        self._kernel_state_engine = KernelStateEngine(scheduler._repository)

        # Initialize handlers for each schedule type
        self._schedule_handlers = {
            ScheduleType.SCHEDULE: ScheduleSessionsHandler(
                scheduler, self, self._scheduling_controller
            ),
            ScheduleType.CHECK_PRECONDITION: CheckPreconditionHandler(
                scheduler, self, self._scheduler_dispatcher, self._scheduling_controller
            ),
            ScheduleType.START: StartSessionsHandler(
                scheduler, self, self._scheduler_dispatcher, self._scheduling_controller
            ),
            ScheduleType.TERMINATE: TerminateSessionsHandler(
                scheduler, self, self._scheduling_controller
            ),
            ScheduleType.SWEEP: SweepSessionsHandler(scheduler),
            ScheduleType.CHECK_PULLING_PROGRESS: CheckPullingProgressHandler(scheduler),
            ScheduleType.CHECK_CREATING_PROGRESS: CheckCreatingProgressHandler(scheduler),
            ScheduleType.CHECK_TERMINATING_PROGRESS: CheckTerminatingProgressHandler(scheduler),
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

            # Execute the handler (includes operation and post-processing)
            with self._operation_metrics.measure_operation(handler.name()):
                await handler.handle()
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
        return await self._kernel_state_engine.mark_kernel_pulling(event)

    async def handle_kernel_creating(self, event: KernelCreatingAnycastEvent) -> bool:
        """Handle kernel creating event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_creating(event)

    async def handle_kernel_running(self, event: KernelStartedAnycastEvent) -> bool:
        """Handle kernel running event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_running(event)

    async def handle_kernel_preparing(self, event: KernelPreparingAnycastEvent) -> bool:
        """Handle kernel preparing event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_preparing(event)

    async def handle_kernel_cancelled(self, event: KernelCancelledAnycastEvent) -> bool:
        """Handle kernel cancelled event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_cancelled(event)

    async def handle_kernel_terminated(self, event: KernelTerminatedAnycastEvent) -> bool:
        """Handle kernel terminated event through the kernel state engine."""
        return await self._kernel_state_engine.mark_kernel_terminated(event)

    async def handle_kernel_heartbeat(self, event: KernelHeartbeatEvent) -> bool:
        """Handle kernel heartbeat event through the kernel state engine."""
        return await self._kernel_state_engine.update_kernel_heartbeat(event)
