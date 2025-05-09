from ai.backend.common.events.events import AbstractEvent
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.types import AgentId


class PropagatorEventDispatcher:
    _event_hub: EventHub

    def __init__(self, event_hub: EventHub) -> None:
        self._event_hub = event_hub

    async def propagate_bgtask_event(
        self,
        context: None,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        await self._event_hub.propagate_event(event)
