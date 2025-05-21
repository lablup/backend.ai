from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from ai.backend.logging import BraceStyleAdapter

from ..events.types import AbstractEvent
from ..types import AgentId
from . import AbstractPlugin, BasePluginContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractEventDispatcherPlugin(AbstractPlugin, metaclass=ABCMeta):
    async def init(self, context: Optional[Any] = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    @abstractmethod
    async def handle_event(
        self,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        raise NotImplementedError


class EventDispatcherPluginContext(BasePluginContext[AbstractEventDispatcherPlugin]):
    plugin_group = "backendai_event_dispatcher_v20"

    async def handle_event(
        self,
        context: None,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        for plugin_instance in self.plugins.values():
            await plugin_instance.handle_event(source, event)
