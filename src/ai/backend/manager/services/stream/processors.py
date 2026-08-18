from collections.abc import Awaitable, Callable

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.session.types import SessionData
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


class StreamProcessors:
    _service: StreamService

    get_streaming_session: SingleEntityActionProcessor[
        GetStreamingSessionAction, GetStreamingSessionActionResult
    ]
    track_connection: SingleEntityActionProcessor[
        TrackConnectionAction, TrackConnectionActionResult
    ]
    untrack_connection: SingleEntityActionProcessor[
        UntrackConnectionAction, UntrackConnectionActionResult
    ]
    gc_stale_connections: ActionProcessor[GCStaleConnectionsAction, GCStaleConnectionsActionResult]
    execute_in_stream: SingleEntityActionProcessor[
        ExecuteInStreamAction, ExecuteInStreamActionResult
    ]
    restart_in_stream: SingleEntityActionProcessor[
        RestartInStreamAction, RestartInStreamActionResult
    ]
    interrupt_in_stream: SingleEntityActionProcessor[
        InterruptInStreamAction, InterruptInStreamActionResult
    ]
    start_service_in_stream: SingleEntityActionProcessor[
        StartServiceInStreamAction, StartServiceInStreamActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[SessionData],
        service: StreamService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self._service = service
        self.get_streaming_session = group.single_entity(
            GetStreamingSessionAction, service.get_streaming_session
        )
        self.track_connection = group.single_entity(TrackConnectionAction, service.track_connection)
        self.untrack_connection = group.single_entity(
            UntrackConnectionAction, service.untrack_connection
        )
        self.gc_stale_connections = ActionProcessor(service.gc_stale_connections, action_monitors)
        self.execute_in_stream = group.single_entity(
            ExecuteInStreamAction, service.execute_in_stream
        )
        self.restart_in_stream = group.single_entity(
            RestartInStreamAction, service.restart_in_stream
        )
        self.interrupt_in_stream = group.single_entity(
            InterruptInStreamAction, service.interrupt_in_stream
        )
        self.start_service_in_stream = group.single_entity(
            StartServiceInStreamAction, service.start_service_in_stream
        )

    def create_connection_refresh_callback(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        service: str,
        stream_id: str,
    ) -> Callable[..., Awaitable[None]]:
        return self._service.create_connection_refresh_callback(
            session_id, kernel_id, service, stream_id
        )
