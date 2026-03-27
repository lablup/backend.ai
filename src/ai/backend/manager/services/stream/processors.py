from collections.abc import Awaitable, Callable
from typing import override

from ai.backend.common.types import KernelId
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.stream.actions.execute_in_stream import (
    ExecuteInStreamAction,
    ExecuteInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.gc_stale_connections import (
    GCStaleConnectionsAction,
    GCStaleConnectionsActionResult,
)
from ai.backend.manager.services.stream.actions.get_streaming_session import (
    GetStreamingSessionAction,
    GetStreamingSessionActionResult,
)
from ai.backend.manager.services.stream.actions.interrupt_in_stream import (
    InterruptInStreamAction,
    InterruptInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.restart_in_stream import (
    RestartInStreamAction,
    RestartInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.start_service_in_stream import (
    StartServiceInStreamAction,
    StartServiceInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.track_connection import (
    TrackConnectionAction,
    TrackConnectionActionResult,
)
from ai.backend.manager.services.stream.actions.untrack_connection import (
    UntrackConnectionAction,
    UntrackConnectionActionResult,
)
from ai.backend.manager.services.stream.service import StreamService


class StreamProcessors(AbstractProcessorPackage):
    _service: StreamService

    get_streaming_session: ActionProcessor[
        GetStreamingSessionAction, GetStreamingSessionActionResult
    ]
    track_connection: ActionProcessor[TrackConnectionAction, TrackConnectionActionResult]
    untrack_connection: ActionProcessor[UntrackConnectionAction, UntrackConnectionActionResult]
    gc_stale_connections: ActionProcessor[GCStaleConnectionsAction, GCStaleConnectionsActionResult]
    execute_in_stream: ActionProcessor[ExecuteInStreamAction, ExecuteInStreamActionResult]
    restart_in_stream: ActionProcessor[RestartInStreamAction, RestartInStreamActionResult]
    interrupt_in_stream: ActionProcessor[InterruptInStreamAction, InterruptInStreamActionResult]
    start_service_in_stream: ActionProcessor[
        StartServiceInStreamAction, StartServiceInStreamActionResult
    ]

    def __init__(self, service: StreamService, action_monitors: list[ActionMonitor]) -> None:
        self._service = service
        self.get_streaming_session = ActionProcessor(service.get_streaming_session, action_monitors)
        self.track_connection = ActionProcessor(service.track_connection, action_monitors)
        self.untrack_connection = ActionProcessor(service.untrack_connection, action_monitors)
        self.gc_stale_connections = ActionProcessor(service.gc_stale_connections, action_monitors)
        self.execute_in_stream = ActionProcessor(service.execute_in_stream, action_monitors)
        self.restart_in_stream = ActionProcessor(service.restart_in_stream, action_monitors)
        self.interrupt_in_stream = ActionProcessor(service.interrupt_in_stream, action_monitors)
        self.start_service_in_stream = ActionProcessor(
            service.start_service_in_stream, action_monitors
        )

    def create_connection_refresh_callback(
        self,
        kernel_id: KernelId,
        service: str,
        stream_id: str,
    ) -> Callable[..., Awaitable[None]]:
        return self._service.create_connection_refresh_callback(kernel_id, service, stream_id)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetStreamingSessionAction.spec(),
            TrackConnectionAction.spec(),
            UntrackConnectionAction.spec(),
            GCStaleConnectionsAction.spec(),
            ExecuteInStreamAction.spec(),
            RestartInStreamAction.spec(),
            InterruptInStreamAction.spec(),
            StartServiceInStreamAction.spec(),
        ]
