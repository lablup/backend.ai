from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.types import AgentId
from ai.backend.manager.errors.common import InternalServerError


class PropagatorEventHandler:
    _event_hub: EventHub

    def __init__(self, event_hub: EventHub) -> None:
        self._event_hub = event_hub

    async def propagate_event(
        self,
        context: None,
        source: AgentId,
        event: AbstractBroadcastEvent,
    ) -> None:
        # Generate events to propagate (default implementation returns [self])
        individual_events = event.generate_events()
        for individual_event in individual_events:
            await self._event_hub.propagate_event(individual_event)

    async def propagate_event_with_close(
        self,
        context: None,
        source: AgentId,
        event: AbstractBroadcastEvent,
    ) -> None:
        # Generate events to propagate (default implementation returns [self])
        individual_events = event.generate_events()
        for individual_event in individual_events:
            await self._event_hub.propagate_event(individual_event)
            # Close each individual event's domain
            domain_id = individual_event.domain_id()
            if domain_id is None:
                raise InternalServerError(
                    f"Event domain ID is None for {individual_event.event_name()}"
                )
            await self._event_hub.close_by_alias(individual_event.event_domain(), domain_id)
