"""Dependency provider for the agent-lost checker timer.

Periodically checks whether agents have exceeded the heartbeat timeout
and fires ``AgentTerminatedEvent`` for any that have.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from aiotools import cancel_and_wait, create_timer
from dateutil.tz import tzutc

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.event_types.agent.anycast import AgentTerminatedEvent
from ai.backend.common.types import AgentId
from ai.backend.manager.api.utils import catch_unexpected

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.events.dispatcher import EventProducer
    from ai.backend.manager.config.provider import ManagerConfigProvider

import logging

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@catch_unexpected(log)
async def _check_agent_lost(
    config_provider: ManagerConfigProvider,
    valkey_live: ValkeyLiveClient,
    event_producer: EventProducer,
    _interval: float,
) -> None:
    try:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=config_provider.config.manager.heartbeat_timeout)

        agent_last_seen = await valkey_live.scan_agent_last_seen()
        for agent_id, prev_timestamp in agent_last_seen:
            prev = datetime.fromtimestamp(prev_timestamp, tzutc())
            if now - prev > timeout:
                await event_producer.anycast_event(
                    AgentTerminatedEvent("agent-lost"),
                    source_override=AgentId(agent_id),
                )
    except asyncio.CancelledError:
        pass


@dataclass
class AgentLostCheckerInput:
    """Input required for agent-lost checker timer setup."""

    config_provider: ManagerConfigProvider
    valkey_live: ValkeyLiveClient
    event_producer: EventProducer


class AgentLostCheckerDependency(
    NonMonitorableDependencyProvider[AgentLostCheckerInput, asyncio.Task[None]]
):
    """Provides a periodic timer that detects agent heartbeat timeouts."""

    @property
    def stage_name(self) -> str:
        return "agent-lost-checker"

    @asynccontextmanager
    async def provide(
        self, setup_input: AgentLostCheckerInput
    ) -> AsyncIterator[asyncio.Task[None]]:
        task = create_timer(
            functools.partial(
                _check_agent_lost,
                setup_input.config_provider,
                setup_input.valkey_live,
                setup_input.event_producer,
            ),
            1.0,
        )
        task.set_name("agent_lost_checker")
        try:
            yield task
        finally:
            await cancel_and_wait(task)
