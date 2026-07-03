from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from typing import Any, override

from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from . import AbstractPlugin, BasePluginContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractEventDispatcherPlugin(AbstractPlugin, metaclass=ABCMeta):
    """Base class for event-dispatcher plugins.

    Lifecycle contract for implementations (in-tree or externally installed):

    - ``init(context=None)`` is called once at plugin discovery time, before
      the host's dependency graph exists. Implementations must tolerate a
      ``None`` context (typically by staying disabled).
    - The host calls ``init`` again with a context mapping after its
      dependencies are ready and **before** any event is delivered, so
      ``init`` must be safely re-entrant. The manager provides at least the
      following keys and may add more; implementations must pick the keys
      they need and tolerate extra ones:

      - ``etcd``: the shared :class:`~ai.backend.common.etcd.AsyncEtcd` client
      - ``config_provider``: the manager configuration provider
      - ``repositories``: the manager repositories container
      - ``processors``: the manager service-layer processors container
      - ``error_log_repository``: shortcut kept for backward compatibility

    - ``handle_event`` receives every event the host forwards and must filter
      by event type (``isinstance``) and return quickly for events it does
      not care about. Exceptions raised here are logged and suppressed by the
      host so that one plugin cannot disturb event handling or sibling
      plugins — do not rely on exceptions for control flow.
    """

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
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
        for plugin_name, plugin_instance in self.plugins.items():
            try:
                await plugin_instance.handle_event(source, event)
            except Exception:
                # A misbehaving plugin must not disturb the surrounding event
                # handler (which would leave the message un-acked and cause
                # redelivery) nor starve sibling plugins of the event.
                log.exception(
                    "event-dispatcher plugin {} failed to handle event {}",
                    plugin_name,
                    event.event_name(),
                )
