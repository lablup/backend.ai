import logging

from ai.backend.common.events.event_types.idle.anycast import DoIdleCheckEvent
from ai.backend.common.events.event_types.kernel.anycast import (
    SessionChannelActivityAnycastEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.idle import AppStreamingStatus, IdleCheckerHost

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
        _context: None,
        _source: AgentId,
        _event: DoIdleCheckEvent,
    ) -> None:
        await self._idle_checker_host.do_idle_check()

    async def handle_channel_activity(
        self,
        _context: None,
        _source: AgentId,
        event: SessionChannelActivityAnycastEvent,
    ) -> None:
        await self._idle_checker_host.update_app_streaming_status(
            event.session_id,
            AppStreamingStatus.HAS_ACTIVE_CONNECTIONS
            if event.open_circuits > 0
            else AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
        )
