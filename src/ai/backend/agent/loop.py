from typing import Any, Mapping

import aiotools

from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
    SessionRestartingEvent,
    SessionScheduledEvent,
    SessionTerminatingEvent,
)
from ai.backend.common.reconcilation_loop import ReconcilationLoop


class Registry:
    pass


class Loop(ReconcilationLoop, Registry):
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    local_config: Mapping[str, Any]

    async def prepare_loop(
        self,
    ):
        async with aiotools.aclosing(self.reconcile(SessionScheduledEvent, 10.0)) as ag:
            async for ev in ag:
                pass

    async def terminate_loop(
        self,
    ):
        async with aiotools.aclosing(self.reconcile(SessionTerminatingEvent, 10.0)) as ag:
            async for ev in ag:
                pass

    async def restart_loop(
        self,
    ):
        async with aiotools.aclosing(self.reconcile(SessionRestartingEvent, 10.0)) as ag:
            async for ev in ag:
                pass
