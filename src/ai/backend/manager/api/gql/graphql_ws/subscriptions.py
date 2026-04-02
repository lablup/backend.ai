"""Per-connection subscription task registry."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine


class SubscriptionRegistry:
    """Tracks active subscription tasks for a single WebSocket connection.

    Created per-connection inside ``GraphQLTransportWSHandler.handle()``
    and discarded when the connection closes.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def start(self, sub_id: str, coro: Coroutine[None, None, None]) -> bool:
        """Create an ``asyncio.Task`` for *coro* and register it under *sub_id*.

        Returns ``True`` if the subscription was started, ``False`` if *sub_id*
        is already active (the coroutine is closed without execution).
        """
        if sub_id in self._tasks:
            coro.close()
            return False
        self._tasks[sub_id] = asyncio.create_task(coro)
        return True

    def cancel(self, sub_id: str) -> None:
        """Cancel and remove the subscription (client-initiated complete)."""
        if sub_id in self._tasks:
            self._tasks.pop(sub_id).cancel()

    def remove(self, sub_id: str) -> None:
        """Remove the subscription without cancelling (task finished naturally)."""
        self._tasks.pop(sub_id, None)

    async def cancel_all(self) -> None:
        """Cancel every active subscription and wait for all tasks to finish."""
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
