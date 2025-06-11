import logging

from ai.backend.common.events.event_types.idle.anycast import DoIdleCheckEvent
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.idle import IdleCheckerHost

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class IdleCheckEventHandler:
    _idle_checker_host: IdleCheckerHost

    def __init__(
        self,
        idle_checker_host: IdleCheckerHost,
    ) -> None:
        self._idle_checker_host = idle_checker_host

    async def handle_do_idle_check(
        self,
        context: None,
        source: AgentId,
        event: DoIdleCheckEvent,
    ) -> None:
        await self._idle_checker_host.do_idle_check()
