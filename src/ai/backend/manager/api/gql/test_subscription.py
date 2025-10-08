"""Test subscription for WebSocket connectivity testing."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncGenerator

import strawberry


@strawberry.type
class TimeUpdate:
    """Simple time update message for testing subscriptions."""

    current_time: str
    counter: int


@strawberry.subscription
async def time_updates(interval: int = 1) -> AsyncGenerator[TimeUpdate, None]:
    """
    Test subscription that emits current time at regular intervals.

    Args:
        interval: Seconds between updates (default: 1)
    """
    counter = 0
    while True:
        counter += 1
        yield TimeUpdate(
            current_time=datetime.now().isoformat(),
            counter=counter,
        )
        await asyncio.sleep(interval)
