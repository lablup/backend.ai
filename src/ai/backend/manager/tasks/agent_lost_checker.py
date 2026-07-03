"""Periodic task that detects agents whose heartbeat has timed out."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final, override

from dateutil.tz import tzutc

from ai.backend.common.cron import PeriodicTask
from ai.backend.common.events.event_types.agent.anycast import AgentTerminatedEvent
from ai.backend.common.types import AgentId

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.events.dispatcher import EventProducer
    from ai.backend.manager.config.provider import ManagerConfigProvider

_CHECK_INTERVAL: Final[float] = 1.0


class AgentLostCheckerTask(PeriodicTask):
    """Detect agents whose heartbeat has timed out and fire termination events."""

    _config_provider: Final[ManagerConfigProvider]
    _valkey_live: Final[ValkeyLiveClient]
    _event_producer: Final[EventProducer]

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        valkey_live: ValkeyLiveClient,
        event_producer: EventProducer,
    ) -> None:
        self._config_provider = config_provider
        self._valkey_live = valkey_live
        self._event_producer = event_producer

    @property
    @override
    def name(self) -> str:
        return "agent_lost_checker"

    @property
    @override
    def interval(self) -> float:
        return _CHECK_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        now = datetime.now(tzutc())
        timeout = timedelta(seconds=self._config_provider.config.manager.heartbeat_timeout)

        agent_last_seen = await self._valkey_live.scan_agent_last_seen()
        for agent_id, prev_timestamp in agent_last_seen:
            prev = datetime.fromtimestamp(prev_timestamp, tzutc())
            if now - prev > timeout:
                await self._event_producer.anycast_event(
                    AgentTerminatedEvent("agent-lost"),
                    source_override=AgentId(agent_id),
                )
