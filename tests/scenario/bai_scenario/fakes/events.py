"""Stand-in for the event producer a session termination reaches.

Marking sessions for termination broadcasts each one's new status. The broadcast leaves
the process through a message queue, so it is replaced with one that sends nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractBroadcastEvent


class SilentEventProducer(EventProducer):
    """브로드캐스트를 받고 아무 데도 보내지 않는다.

    실물의 초기화는 메시지 큐를 받으므로 부르지 않는다.
    """

    def __init__(self) -> None:
        pass

    @override
    async def broadcast_events_batch(self, events: Sequence[AbstractBroadcastEvent]) -> None:
        return None
