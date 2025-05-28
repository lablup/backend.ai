from dataclasses import dataclass

from ai.backend.common.events.agent import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.events.bgtask import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.events.dispatcher import (
    CoalescingOptions,
    EventDispatcher,
)
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.idle import DoIdleCheckEvent
from ai.backend.common.events.image import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.events.kernel import (
    DoSyncKernelLogsEvent,
    KernelCancelledEvent,
    KernelCreatingEvent,
    KernelHeartbeatEvent,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    KernelTerminatingEvent,
)
from ai.backend.common.events.model_serving import (
    ModelServiceStatusEvent,
    RouteCreatedEvent,
)
from ai.backend.common.events.schedule import (
    DoCheckPrecondEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.session import (
    DoTerminateSessionEvent,
    DoUpdateSessionStatusEvent,
    ExecutionCancelledEvent,
    ExecutionFinishedEvent,
    ExecutionStartedEvent,
    ExecutionTimeoutEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionFailureEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionStartedEvent,
    SessionSuccessEvent,
    SessionTerminatedEvent,
    SessionTerminatingEvent,
)
from ai.backend.common.events.vfolder import (
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.manager.event_dispatcher.handlers.propagator import PropagatorEventHandler
from ai.backend.manager.event_dispatcher.handlers.schedule import ScheduleEventHandler
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher

from ..models.utils import ExtendedAsyncSAEngine
from .handlers.agent import AgentEventHandler
from .handlers.idle_check import IdleCheckEventHandler
from .handlers.image import ImageEventHandler
from .handlers.kernel import KernelEventHandler
from .handlers.model_serving import ModelServingEventHandler
from .handlers.plugin import PluginEventHandler
from .handlers.session import SessionEventHandler
from .handlers.vfolder import VFolderEventHandler
from .reporters import EventLogger


@dataclass
class DispatcherArgs:
    scheduler_dispatcher: SchedulerDispatcher
    event_hub: EventHub
    agent_registry: AgentRegistry
    db: ExtendedAsyncSAEngine
    idle_checker_host: IdleCheckerHost
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext


class Dispatchers:
    _db: ExtendedAsyncSAEngine
    _propagator_handler: PropagatorEventHandler
    _agent_event_handler: AgentEventHandler
    _image_event_handler: ImageEventHandler
    _kernel_event_handler: KernelEventHandler
    _schedule_event_handler: ScheduleEventHandler
    _model_serving_event_handler: ModelServingEventHandler
    _session_event_handler: SessionEventHandler
    _vfolder_event_handler: VFolderEventHandler
    _idle_check_event_handler: IdleCheckEventHandler

    def __init__(self, args: DispatcherArgs) -> None:
        """
        Initialize the Dispatchers with the given arguments.
        """
        self._db = args.db
        self._plugin_event_handler = PluginEventHandler(args.event_dispatcher_plugin_ctx)
        self._propagator_handler = PropagatorEventHandler(args.event_hub)
        self._agent_event_handler = AgentEventHandler(args.agent_registry, args.db)
        self._image_event_handler = ImageEventHandler(args.agent_registry, args.db)
        self._kernel_event_handler = KernelEventHandler(args.agent_registry, args.db)
        self._schedule_event_handler = ScheduleEventHandler(args.scheduler_dispatcher)
        self._model_serving_event_handler = ModelServingEventHandler(args.agent_registry, args.db)
        self._session_event_handler = SessionEventHandler(args.agent_registry, args.db)
        self._vfolder_event_handler = VFolderEventHandler(args.db)
        self._idle_check_event_handler = IdleCheckEventHandler(args.idle_checker_host)

    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        """
        Dispatch events to the appropriate dispatcher.
        """
        self._dispatch_bgtask_events(event_dispatcher)
        self._dispatch_agent_events(event_dispatcher)
        self._dispatch_error_monitor_events(event_dispatcher)
        self._dispatch_image_events(event_dispatcher)
        self._dispatch_kernel_events(event_dispatcher)
        self._dispatch_schedule_events(event_dispatcher)
        self._dispatch_model_serving_events(event_dispatcher)
        self._dispatch_session_events(event_dispatcher)
        self._dispatch_session_execution_events(event_dispatcher)
        self._dispatch_vfolder_events(event_dispatcher)
        self._dispatch_idle_check_events(event_dispatcher)

    def _dispatch_bgtask_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        """
        Register event dispatchers for background task events.
        """
        event_dispatcher.subscribe(
            BgtaskUpdatedEvent, None, self._propagator_handler.propagate_event
        )
        event_dispatcher.subscribe(BgtaskDoneEvent, None, self._propagator_handler.propagate_event)
        event_dispatcher.subscribe(
            BgtaskPartialSuccessEvent,
            None,
            self._propagator_handler.propagate_event,
        )
        event_dispatcher.subscribe(
            BgtaskCancelledEvent, None, self._propagator_handler.propagate_event
        )
        event_dispatcher.subscribe(
            BgtaskFailedEvent, None, self._propagator_handler.propagate_event
        )

    def _dispatch_agent_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        # action-trigerring events
        event_dispatcher.consume(
            DoAgentResourceCheckEvent, None, self._agent_event_handler.handle_check_agent_resource
        )
        # heartbeat events
        event_dispatcher.consume(
            AgentHeartbeatEvent, None, self._agent_event_handler.handle_agent_heartbeat
        )

        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(AgentStartedEvent, None, self._agent_event_handler.handle_agent_started)
        evd.consume(AgentTerminatedEvent, None, self._agent_event_handler.handle_agent_terminated)
        evd.consume(
            AgentImagesRemoveEvent, None, self._agent_event_handler.handle_agent_images_remove
        )

    def _dispatch_error_monitor_events(self, event_dispatcher: EventDispatcher) -> None:
        evd = event_dispatcher.with_reporters([
            EventLogger(self._db),
        ])
        evd.consume(
            AgentErrorEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="agent.error",
        )

    def _dispatch_image_events(self, event_dispatcher: EventDispatcher) -> None:
        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            ImagePullStartedEvent,
            None,
            self._image_event_handler.handle_image_pull_started,
            name="api.session.ipullst",
        )
        evd.consume(
            ImagePullFinishedEvent,
            None,
            self._image_event_handler.handle_image_pull_finished,
            name="api.session.ipullfin",
        )
        evd.consume(
            ImagePullFailedEvent,
            None,
            self._image_event_handler.handle_image_pull_failed,
            name="api.session.ipullfail",
        )

    def _dispatch_kernel_events(self, event_dispatcher: EventDispatcher) -> None:
        # action-trigerring events
        event_dispatcher.consume(
            DoSyncKernelLogsEvent,
            None,
            self._kernel_event_handler.handle_kernel_log,
            name="api.session.syncklog",
        )

        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            KernelPreparingEvent,
            None,
            self._kernel_event_handler.handle_kernel_preparing,
            name="api.session.kprep",
        )
        evd.consume(
            KernelPullingEvent,
            None,
            self._kernel_event_handler.handle_kernel_pulling,
            name="api.session.kpull",
        )
        evd.consume(
            KernelCreatingEvent,
            None,
            self._kernel_event_handler.handle_kernel_creating,
            name="api.session.kcreat",
        )
        evd.consume(
            KernelStartedEvent,
            None,
            self._kernel_event_handler.handle_kernel_started,
            name="api.session.kstart",
        )
        evd.consume(
            KernelCancelledEvent,
            None,
            self._kernel_event_handler.handle_kernel_cancelled,
            name="api.session.kstart",
        )
        evd.consume(
            KernelTerminatingEvent,
            None,
            self._kernel_event_handler.handle_kernel_terminating,
            name="api.session.kterming",
        )
        evd.consume(
            KernelTerminatedEvent,
            None,
            self._kernel_event_handler.handle_kernel_terminated,
            name="api.session.kterm",
        )
        evd.consume(
            KernelHeartbeatEvent,
            None,
            self._kernel_event_handler.handle_kernel_heartbeat,
            name="api.session.kheartbeat",
        )

    def _dispatch_model_serving_events(self, event_dispatcher: EventDispatcher) -> None:
        event_dispatcher.consume(
            ModelServiceStatusEvent,
            None,
            self._model_serving_event_handler.handle_model_service_status_update,
        )
        event_dispatcher.consume(
            RouteCreatedEvent, None, self._model_serving_event_handler.handle_route_creation
        )

    def _dispatch_schedule_events(self, event_dispatcher: EventDispatcher) -> None:
        coalescing_opts: CoalescingOptions = {
            "max_wait": 0.5,
            "max_batch_size": 32,
        }
        event_dispatcher.consume(
            SessionEnqueuedEvent,
            None,
            self._schedule_event_handler.handle_session_enqueued,
            coalescing_opts,
            name="dispatcher.schedule/enqueue",
        )
        event_dispatcher.consume(
            SessionTerminatedEvent,
            None,
            self._schedule_event_handler.handle_session_terminated,
            coalescing_opts,
            name="dispatcher.term",
        )
        event_dispatcher.consume(
            AgentStartedEvent,
            None,
            self._schedule_event_handler.handle_agent_started,
            name="dispatcher.schedule",
        )
        event_dispatcher.consume(
            DoScheduleEvent, None, self._schedule_event_handler.handle_do_schedule, coalescing_opts
        )
        event_dispatcher.consume(
            DoStartSessionEvent, None, self._schedule_event_handler.handle_do_start_session
        )
        event_dispatcher.consume(
            DoCheckPrecondEvent, None, self._schedule_event_handler.handle_do_check_precond
        )
        event_dispatcher.consume(DoScaleEvent, None, self._schedule_event_handler.handle_do_scale)
        event_dispatcher.consume(
            DoUpdateSessionStatusEvent,
            None,
            self._schedule_event_handler.handle_do_update_session_status,
        )

    def _dispatch_session_events(self, event_dispatcher: EventDispatcher) -> None:
        # action-trigerring events
        event_dispatcher.consume(
            DoTerminateSessionEvent,
            None,
            self._session_event_handler.handle_destroy_session,
            name="api.session.doterm",
        )

        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            SessionStartedEvent,
            None,
            self._session_event_handler.handle_session_started,
            name="api.session.sstart",
        )
        evd.consume(
            SessionCancelledEvent,
            None,
            self._session_event_handler.handle_session_cancelled,
            name="api.session.scancel",
        )
        evd.consume(
            SessionTerminatingEvent,
            None,
            self._session_event_handler.handle_session_terminating,
            name="api.session.sterming",
        )
        evd.consume(
            SessionTerminatedEvent,
            None,
            self._session_event_handler.handle_session_terminated,
            name="api.session.sterm",
        )
        evd.consume(SessionEnqueuedEvent, None, self._session_event_handler.invoke_session_callback)
        evd.consume(
            SessionScheduledEvent, None, self._session_event_handler.invoke_session_callback
        )
        evd.consume(
            SessionPreparingEvent, None, self._session_event_handler.invoke_session_callback
        )
        evd.consume(SessionSuccessEvent, None, self._session_event_handler.handle_batch_result)
        evd.consume(SessionFailureEvent, None, self._session_event_handler.handle_batch_result)

    def _dispatch_vfolder_events(self, event_dispatcher: EventDispatcher) -> None:
        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            VFolderDeletionSuccessEvent,
            None,
            self._vfolder_event_handler.handle_vfolder_deletion_success,
        )
        evd.consume(
            VFolderDeletionFailureEvent,
            None,
            self._vfolder_event_handler.handle_vfolder_deletion_failure,
        )

    def _dispatch_session_execution_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        evd = event_dispatcher.with_reporters([
            EventLogger(self._db),
        ])
        evd.consume(
            SessionStartedEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="session_execution.started",
        )
        evd.consume(
            ExecutionStartedEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="session_execution.started",
        )
        evd.consume(
            ExecutionFinishedEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="session_execution.finished",
        )
        evd.consume(
            ExecutionTimeoutEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="session_execution.timeout",
        )
        evd.consume(
            ExecutionCancelledEvent,
            None,
            self._plugin_event_handler.handle_event,
            name="session_execution.cancelled",
        )

    def _dispatch_idle_check_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        event_dispatcher.consume(
            DoIdleCheckEvent,
            None,
            self._idle_check_event_handler.handle_do_idle_check,
            name="idle_check",
        )
