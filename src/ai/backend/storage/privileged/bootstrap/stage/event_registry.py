from dataclasses import dataclass
from typing import override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import AgentId

from ...event_dispatcher.dispatch import Dispatchers

SOURCE_ID = AgentId("storage-proxy-privileged")


@dataclass
class EventRegistrySpec:
    bgtask_mgr: BackgroundTaskManager
    event_dispatcher: EventDispatcher


@dataclass
class EventRegistryResult:
    event_dispatcher: EventDispatcher


class EventRegistrySpecGenerator(ArgsSpecGenerator[EventRegistrySpec]):
    pass


class EventRegistryProvisioner(Provisioner[EventRegistrySpec, EventRegistryResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-event-registry"

    @override
    async def setup(self, spec: EventRegistrySpec) -> EventRegistryResult:
        dispatchers = Dispatchers(spec.bgtask_mgr)
        dispatchers.dispatch(spec.event_dispatcher)
        await spec.event_dispatcher.start()
        return EventRegistryResult(spec.event_dispatcher)

    @override
    async def teardown(self, resource: EventRegistryResult) -> None:
        pass


class EventRegistryStage(ProvisionStage[EventRegistrySpec, EventRegistryResult]):
    pass
