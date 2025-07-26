from dataclasses import dataclass
from typing import override

from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.stage.types import Provisioner


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
