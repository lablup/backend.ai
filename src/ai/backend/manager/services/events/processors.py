from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
    resolve_session: ActionProcessor[
        ResolveSessionForEventsAction, ResolveSessionForEventsActionResult
    ]
    resolve_group: ActionProcessor[ResolveGroupForEventsAction, ResolveGroupForEventsActionResult]

    def __init__(self, service: EventsService, action_monitors: list[ActionMonitor]) -> None:
        self.resolve_session = ActionProcessor(service.resolve_session_for_events, action_monitors)
        self.resolve_group = ActionProcessor(service.resolve_group_for_events, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ResolveSessionForEventsAction.spec(),
            ResolveGroupForEventsAction.spec(),
        ]
