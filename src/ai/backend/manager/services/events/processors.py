from collections.abc import Mapping
from typing import Any, override

from aiohttp_sse import EventSourceResponse

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.events.hub.propagators.session import SessionEventPropagator
from ai.backend.manager.services.events.actions.resolve_group_for_events import (
    ResolveGroupForEventsAction,
    ResolveGroupForEventsActionResult,
)
from ai.backend.manager.services.events.actions.resolve_session_for_events import (
    ResolveSessionForEventsAction,
    ResolveSessionForEventsActionResult,
)
from ai.backend.manager.services.events.service import EventsService


class EventsProcessors(AbstractProcessorPackage):
    _service: EventsService

    resolve_session: ActionProcessor[
        ResolveSessionForEventsAction, ResolveSessionForEventsActionResult
    ]
    resolve_group: ActionProcessor[ResolveGroupForEventsAction, ResolveGroupForEventsActionResult]

    def __init__(self, service: EventsService, action_monitors: list[ActionMonitor]) -> None:
        self._service = service
        self.resolve_session = ActionProcessor(service.resolve_session_for_events, action_monitors)
        self.resolve_group = ActionProcessor(service.resolve_group_for_events, action_monitors)

    def create_session_propagator(
        self,
        response: EventSourceResponse,
        filters: Mapping[str, Any],
    ) -> SessionEventPropagator:
        return self._service.create_session_propagator(response, filters)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveSessionForEventsAction.spec(),
            ResolveGroupForEventsAction.spec(),
        ]
