from dataclasses import dataclass
from typing import override

from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator


@dataclass
class EventHubSpec:
    pass


class EventHubProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "event-hub-provisioner"

    @override
    async def setup(self, spec: EventHubSpec) -> EventHub:
        event_hub = EventHub()
        return event_hub

    @override
    async def teardown(self, resource: EventHub) -> None:
        await resource.shutdown()


class EventHubSpecGenerator(SpecGenerator[EventHubSpec]):
    def __init__(self):
        pass

    @override
    async def wait_for_spec(self) -> EventHubSpec:
        return EventHubSpec()


# Type alias for EventHub stage
EventHubStage = ProvisionStage[EventHubSpec, EventHub]
