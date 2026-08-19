"""Dependency provider for the agent-lost checker timer.

Periodically checks whether agents have exceeded the heartbeat timeout
and fires ``AgentTerminatedEvent`` for any that have.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.cron import LocalCron
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.tasks.agent_lost_checker import AgentLostCheckerTask

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.events.dispatcher import EventProducer
    from ai.backend.manager.config.provider import ManagerConfigProvider


@dataclass
class AgentLostCheckerInput:
    """Input required for agent-lost checker timer setup."""

    config_provider: ManagerConfigProvider
    valkey_live: ValkeyLiveClient
    event_producer: EventProducer


class AgentLostCheckerDependency(
    NonMonitorableDependencyProvider[AgentLostCheckerInput, LocalCron]
):
    """Provides a periodic timer that detects agent heartbeat timeouts."""

    @property
    @override
    def stage_name(self) -> str:
        return "agent-lost-checker"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: AgentLostCheckerInput) -> AsyncIterator[LocalCron]:
        cron = LocalCron([
            AgentLostCheckerTask(
                setup_input.config_provider,
                setup_input.valkey_live,
                setup_input.event_producer,
            )
        ])
        await cron.start()
        try:
            yield cron
        finally:
            await cron.stop()
