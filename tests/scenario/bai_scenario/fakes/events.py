"""Stand-in for the event producer a write hands its status transitions to.

The real one needs a message queue and sends every event out of the process. This one
keeps what it was handed and sends nothing, so a row can see which events a write
broadcast without a queue behind it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractAnycastEvent, AbstractBroadcastEvent
from ai.backend.common.types import AgentId


class RecordingEventProducer(EventProducer):
    """보낸 이벤트를 받아 적기만 한다. 실물의 초기화는 메시지 큐를 요구하므로 부르지 않는다."""

    broadcast: list[AbstractBroadcastEvent]
    anycast: list[AbstractAnycastEvent]

    def __init__(self) -> None:
        self.broadcast = []
        self.anycast = []

    @override
    async def close(self) -> None:
        return

    @override
    async def anycast_event(
        self,
        event: AbstractAnycastEvent,
        source_override: AgentId | None = None,
    ) -> None:
        self.anycast.append(event)

    @override
    async def broadcast_event(
        self,
        event: AbstractBroadcastEvent,
        source_override: AgentId | None = None,
    ) -> None:
        self.broadcast.append(event)

    @override
    async def broadcast_event_with_cache(
        self,
        cache_id: str,
        event: AbstractBroadcastEvent,
    ) -> None:
        self.broadcast.append(event)

    @override
    async def broadcast_events_batch(
        self,
        events: Sequence[AbstractBroadcastEvent],
    ) -> None:
        self.broadcast.extend(events)

    @override
    async def anycast_and_broadcast_event(
        self,
        anycast_event: AbstractAnycastEvent,
        broadcast_event: AbstractBroadcastEvent,
    ) -> None:
        self.anycast.append(anycast_event)
        self.broadcast.append(broadcast_event)
