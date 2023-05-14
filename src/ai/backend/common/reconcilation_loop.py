from __future__ import annotations

import asyncio

import aiotools

from ai.backend.common.events import (
    AbstractEvent,
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.types import aobject


class NoopEvent(AbstractEvent):
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple) -> NoopEvent:
        return cls()


class ReconcilationLoop(aobject):
    event_dispatcher: EventDispatcher
    event_producer: EventProducer

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
    ) -> None:
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer

    async def __ainit__(self) -> None:
        return

    async def aclose(self) -> None:
        return

    async def reconcile(self, event: type[AbstractEvent], interval: float = 10.0):
        while True:
            ev = await aiotools.race(
                self.event_dispatcher.wait(event), asyncio.sleep(interval, NoopEvent())
            )
            yield ev
