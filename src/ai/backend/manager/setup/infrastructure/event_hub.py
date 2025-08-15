from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.stage.types import Provisioner


@dataclass
class EventHubSpec:
    pass  # EventHub has no initialization parameters


class EventHubProvisioner(Provisioner[EventHubSpec, EventHub]):
    @property
    def name(self) -> str:
        return "event_hub"

    async def setup(self, spec: EventHubSpec) -> EventHub:
        return EventHub()

    async def teardown(self, resource: EventHub) -> None:
        await resource.shutdown()
