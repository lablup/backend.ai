from __future__ import annotations

import asyncio

import pytest

from ai.backend.kube.controller.runner import WorkQueue


@pytest.fixture
def queue() -> WorkQueue:
    return WorkQueue()


class TestWorkQueue:
    async def test_deduplicates_queued_keys(self, queue: WorkQueue) -> None:
        queue.add(("ns", "a"))
        queue.add(("ns", "a"))
        assert await queue.get() == ("ns", "a")
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(queue.get(), 0.05)

    async def test_key_changed_while_active_is_requeued(self, queue: WorkQueue) -> None:
        queue.add(("ns", "a"))
        key = await queue.get()
        queue.add(key)
        queue.done(key)
        assert await asyncio.wait_for(queue.get(), 0.05) == key
