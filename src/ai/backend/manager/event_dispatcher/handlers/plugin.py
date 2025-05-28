import logging

from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PluginEventHandler:
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext

    def __init__(self, _event_dispatcher_plugin_ctx: EventDispatcherPluginContext) -> None:
        self._event_dispatcher_plugin_ctx = _event_dispatcher_plugin_ctx

    async def handle_event(
        self,
        context: None,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        await self._event_dispatcher_plugin_ctx.handle_event(context, source, event)
