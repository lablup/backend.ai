import logging

from ai.backend.common.events.event_types.session.anycast import (
    DoRecalculateUsageEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UsageEventHandler:
    _agent_registry: AgentRegistry

    def __init__(self, agent_registry: AgentRegistry) -> None:
        self._agent_registry = agent_registry

    async def handle_do_recalculate_usage(
        self, context: None, agent_id: str, ev: DoRecalculateUsageEvent
    ) -> None:
        await self._agent_registry.recalc_resource_usage(do_fullscan=True)
