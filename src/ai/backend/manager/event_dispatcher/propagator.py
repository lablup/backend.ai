from ai.backend.common.events.dispatcher import AbstractEvent
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.types import AgentId
from ai.backend.manager.errors.exceptions import InternalServerError


class PropagatorEventDispatcher:
    _event_hub: EventHub

    def __init__(self, event_hub: EventHub) -> None:
        self._event_hub = event_hub

    async def propagate_event(
        self,
        context: None,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        await self._event_hub.propagate_event(event)

    async def propagate_event_with_close(
        self,
        context: None,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        await self._event_hub.propagate_event(event)
        domain_id = event.domain_id()
        if domain_id is None:
            raise InternalServerError("Event domain ID is None")
        await self._event_hub.close_by_alias(event.event_domain(), domain_id)
