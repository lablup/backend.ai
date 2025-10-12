from dataclasses import dataclass
from typing import Callable

from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.events.dispatcher import (
    CoalescingOptions,
    EventDispatcher,
)
from ai.backend.common.events.event_types.agent.anycast import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentStartedEvent,
    AgentStatusHeartbeat,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.events.event_types.artifact.anycast import (
    ModelImportDoneEvent,
    ModelMetadataFetchDoneEvent,
)
from ai.backend.common.events.event_types.artifact_registry.anycast import (
    DoScanReservoirRegistryEvent,
)
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.events.event_types.idle.anycast import DoIdleCheckEvent
from ai.backend.common.events.event_types.image.anycast import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.events.event_types.kernel.anycast import (
    DoSyncKernelLogsEvent,
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelHeartbeatEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
    KernelTerminatingAnycastEvent,
)
from ai.backend.common.events.event_types.model_serving.anycast import (
    ModelServiceStatusAnycastEvent,
    RouteCreatedAnycastEvent,
)
from ai.backend.common.events.event_types.schedule.anycast import (
    DoCheckPrecondEvent,
    DoDeploymentLifecycleEvent,
    DoDeploymentLifecycleIfNeededEvent,
    DoRouteLifecycleEvent,
    DoRouteLifecycleIfNeededEvent,
    DoScaleEvent,
    DoScheduleEvent,
    DoSokovanProcessIfNeededEvent,
    DoSokovanProcessScheduleEvent,
    DoStartSessionEvent,
)
from ai.backend.common.events.event_types.session.anycast import (
    DoTerminateSessionEvent,
    DoUpdateSessionStatusEvent,
    ExecutionCancelledAnycastEvent,
    ExecutionFinishedAnycastEvent,
    ExecutionStartedAnycastEvent,
    ExecutionTimeoutAnycastEvent,
    SessionCancelledAnycastEvent,
    SessionCheckingPrecondAnycastEvent,
    SessionEnqueuedAnycastEvent,
    SessionFailureAnycastEvent,
    SessionPreparingAnycastEvent,
    SessionScheduledAnycastEvent,
    SessionStartedAnycastEvent,
    SessionSuccessAnycastEvent,
    SessionTerminatedAnycastEvent,
    SessionTerminatingAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderCloneFailureEvent,
    VFolderCloneSuccessEvent,
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.event_dispatcher.handlers.artifact import ArtifactEventHandler
from ai.backend.manager.event_dispatcher.handlers.artifact_registry import (
    ArtifactRegistryEventHandler,
)
from ai.backend.manager.event_dispatcher.handlers.propagator import PropagatorEventHandler
from ai.backend.manager.event_dispatcher.handlers.schedule import ScheduleEventHandler
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from ..models.utils import ExtendedAsyncSAEngine
from .handlers.agent import AgentEventHandler
from .handlers.idle_check import IdleCheckEventHandler
from .handlers.image import ImageEventHandler
from .handlers.kernel import KernelEventHandler
from .handlers.model_serving import ModelServingEventHandler
from .handlers.session import SessionEventHandler
from .handlers.vfolder import VFolderEventHandler
from .reporters import EventLogger


@dataclass
class DispatcherArgs:
    valkey_container_log: ValkeyContainerLogClient
    valkey_stat: ValkeyStatClient
    valkey_stream: ValkeyStreamClient
    scheduler_dispatcher: SchedulerDispatcher
    schedule_coordinator: ScheduleCoordinator
    scheduling_controller: SchedulingController
    deployment_coordinator: DeploymentCoordinator
    route_coordinator: RouteCoordinator
    scheduler_repository: SchedulerRepository
    event_hub: EventHub
    agent_registry: AgentRegistry
    db: ExtendedAsyncSAEngine
    idle_checker_host: IdleCheckerHost
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    repositories: Repositories
    processors_factory: Callable[[], Processors]
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    use_sokovan: bool = True


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
    _artifact_event_handler: ArtifactEventHandler
    _artifact_registry_event_handler: ArtifactRegistryEventHandler

    def __init__(self, args: DispatcherArgs) -> None:
        """
        Initialize the Dispatchers with the given arguments.
        """
        self._db = args.db
        self._propagator_handler = PropagatorEventHandler(args.event_hub)
        self._agent_event_handler = AgentEventHandler(
            args.agent_registry, args.db, args.event_dispatcher_plugin_ctx, args.processors_factory
        )
        self._image_event_handler = ImageEventHandler(
            args.agent_registry,
            args.db,
            args.use_sokovan,
            args.schedule_coordinator,
        )

        self._kernel_event_handler = KernelEventHandler(
            args.valkey_container_log,
            args.valkey_stat,
            args.valkey_stream,
            args.agent_registry,
            args.db,
            args.schedule_coordinator,
            args.use_sokovan,
        )
        self._schedule_event_handler = ScheduleEventHandler(
            args.scheduler_dispatcher,
            args.schedule_coordinator,
            args.scheduling_controller,
            args.deployment_coordinator,
            args.route_coordinator,
            args.event_hub,
            args.use_sokovan,
        )
        self._model_serving_event_handler = ModelServingEventHandler(args.agent_registry, args.db)
        self._session_event_handler = SessionEventHandler(
            args.agent_registry,
            args.db,
            args.event_dispatcher_plugin_ctx,
            args.idle_checker_host,
        )
        self._vfolder_event_handler = VFolderEventHandler(args.db)
        self._idle_check_event_handler = IdleCheckEventHandler(args.idle_checker_host)
        self._artifact_event_handler = ArtifactEventHandler(
            args.repositories.artifact.repository,
            args.repositories.huggingface_registry.repository,
            args.repositories.reservoir_registry.repository,
            args.config_provider,
        )
        self._artifact_registry_event_handler = ArtifactRegistryEventHandler(
            args.processors_factory,
            args.repositories.artifact.repository,
            args.repositories.artifact_registry.repository,
            args.repositories.reservoir_registry.repository,
            args.repositories.object_storage.repository,
            args.storage_manager,
        )

    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        """
        Dispatch events to the appropriate dispatcher.
        """
        self._dispatch_bgtask_events(event_dispatcher)
        self._dispatch_agent_events(event_dispatcher)
        self._dispatch_image_events(event_dispatcher)
        self._dispatch_kernel_events(event_dispatcher)
        self._dispatch_schedule_events(event_dispatcher)
        self._dispatch_model_serving_events(event_dispatcher)
        self._dispatch_session_events(event_dispatcher)
        self._dispatch_vfolder_events(event_dispatcher)
        self._dispatch_idle_check_events(event_dispatcher)
        self._dispatch_artifact_events(event_dispatcher)
        self._dispatch_artifact_registry_events(event_dispatcher)

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
        event_dispatcher.consume(
            AgentStatusHeartbeat,
            None,
            self._agent_event_handler.handle_agent_container_heartbeat,
            name="agent.status_heartbeat",
        )

        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(AgentStartedEvent, None, self._agent_event_handler.handle_agent_started)
        evd.consume(AgentTerminatedEvent, None, self._agent_event_handler.handle_agent_terminated)
        evd.consume(
            AgentImagesRemoveEvent, None, self._agent_event_handler.handle_agent_images_remove
        )
        evd.consume(
            AgentErrorEvent,
            None,
            self._agent_event_handler.handle_agent_error,
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
            KernelPreparingAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_preparing,
            name="api.session.kprep",
        )
        evd.consume(
            KernelPullingAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_pulling,
            name="api.session.kpull",
        )
        evd.consume(
            KernelCreatingAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_creating,
            name="api.session.kcreat",
        )
        evd.consume(
            KernelStartedAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_started,
            name="api.session.kstart",
        )
        evd.consume(
            KernelCancelledAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_cancelled,
            name="api.session.kstart",
        )
        evd.consume(
            KernelTerminatingAnycastEvent,
            None,
            self._kernel_event_handler.handle_kernel_terminating,
            name="api.session.kterming",
        )
        evd.consume(
            KernelTerminatedAnycastEvent,
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
            ModelServiceStatusAnycastEvent,
            None,
            self._model_serving_event_handler.handle_model_service_status_update,
        )
        event_dispatcher.consume(
            RouteCreatedAnycastEvent, None, self._model_serving_event_handler.handle_route_creation
        )

    def _dispatch_schedule_events(self, event_dispatcher: EventDispatcher) -> None:
        coalescing_opts: CoalescingOptions = {
            "max_wait": 0.5,
            "max_batch_size": 32,
        }
        event_dispatcher.consume(
            SessionEnqueuedAnycastEvent,
            None,
            self._schedule_event_handler.handle_session_enqueued,
            coalescing_opts,
            name="dispatcher.schedule/enqueue",
        )
        event_dispatcher.consume(
            SessionTerminatedAnycastEvent,
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
        # Sokovan scheduler events
        event_dispatcher.consume(
            DoSokovanProcessIfNeededEvent,
            None,
            self._schedule_event_handler.handle_do_sokovan_process_if_needed,
            name="sokovan.process_if_needed",
        )
        event_dispatcher.consume(
            DoSokovanProcessScheduleEvent,
            None,
            self._schedule_event_handler.handle_do_sokovan_process_schedule,
            name="sokovan.process_schedule",
        )
        # Subscribe to SchedulingBroadcastEvent to propagate individual events
        event_dispatcher.subscribe(
            SchedulingBroadcastEvent,
            None,
            self._schedule_event_handler.handle_scheduling_broadcast,
        )
        # Deployment lifecycle events
        event_dispatcher.consume(
            DoDeploymentLifecycleIfNeededEvent,
            None,
            self._schedule_event_handler.handle_do_deployment_lifecycle_if_needed,
            name="deployment.lifecycle_if_needed",
        )
        event_dispatcher.consume(
            DoDeploymentLifecycleEvent,
            None,
            self._schedule_event_handler.handle_do_deployment_lifecycle,
            name="deployment.lifecycle",
        )
        # Route lifecycle events
        event_dispatcher.consume(
            DoRouteLifecycleIfNeededEvent,
            None,
            self._schedule_event_handler.handle_do_route_lifecycle_if_needed,
            name="route.lifecycle_if_needed",
        )
        event_dispatcher.consume(
            DoRouteLifecycleEvent,
            None,
            self._schedule_event_handler.handle_do_route_lifecycle,
            name="route.lifecycle",
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
            SessionStartedAnycastEvent,
            None,
            self._session_event_handler.handle_session_started,
            name="api.session.sstart",
        )
        evd.consume(
            SessionCancelledAnycastEvent,
            None,
            self._session_event_handler.handle_session_cancelled,
            name="api.session.scancel",
        )
        evd.consume(
            SessionTerminatingAnycastEvent,
            None,
            self._session_event_handler.handle_session_terminating,
            name="api.session.sterming",
        )
        evd.consume(
            SessionTerminatedAnycastEvent,
            None,
            self._session_event_handler.handle_session_terminated,
            name="api.session.sterm",
        )
        evd.consume(
            SessionEnqueuedAnycastEvent, None, self._session_event_handler.invoke_session_callback
        )
        evd.consume(
            SessionScheduledAnycastEvent, None, self._session_event_handler.invoke_session_callback
        )
        evd.consume(
            SessionCheckingPrecondAnycastEvent,
            None,
            self._session_event_handler.invoke_session_callback,
        )
        evd.consume(
            SessionPreparingAnycastEvent, None, self._session_event_handler.invoke_session_callback
        )
        evd.consume(
            SessionSuccessAnycastEvent, None, self._session_event_handler.handle_batch_result
        )
        evd.consume(
            SessionFailureAnycastEvent, None, self._session_event_handler.handle_batch_result
        )
        evd.consume(
            ExecutionStartedAnycastEvent,
            None,
            self._session_event_handler.handle_execution_started,
            name="session_execution.started",
        )
        evd.consume(
            ExecutionFinishedAnycastEvent,
            None,
            self._session_event_handler.handle_execution_finished,
            name="session_execution.finished",
        )
        evd.consume(
            ExecutionTimeoutAnycastEvent,
            None,
            self._session_event_handler.handle_execution_timeout,
            name="session_execution.timeout",
        )
        evd.consume(
            ExecutionCancelledAnycastEvent,
            None,
            self._session_event_handler.handle_execution_cancelled,
            name="session_execution.cancelled",
        )

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
        evd.consume(
            VFolderCloneSuccessEvent,
            None,
            self._vfolder_event_handler.handle_vfolder_clone_success,
        )
        evd.consume(
            VFolderCloneFailureEvent,
            None,
            self._vfolder_event_handler.handle_vfolder_clone_failure,
        )

    def _dispatch_artifact_events(self, event_dispatcher: EventDispatcher) -> None:
        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            ModelMetadataFetchDoneEvent,
            None,
            self._artifact_event_handler.handle_model_metadata_fetch_done,
        )
        evd.consume(
            ModelImportDoneEvent,
            None,
            self._artifact_event_handler.handle_model_import_done,
        )

    def _dispatch_artifact_registry_events(self, event_dispatcher: EventDispatcher) -> None:
        evd = event_dispatcher.with_reporters([EventLogger(self._db)])
        evd.consume(
            DoScanReservoirRegistryEvent,
            None,
            self._artifact_registry_event_handler.handle_artifact_registry_scan,
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
