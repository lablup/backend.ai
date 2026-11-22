from __future__ import annotations

import asyncio

import pytest

from ai.backend.kube.controller.runner import WorkQueue, retry_delay


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


class TestRetryDelay:
    def test_doubles_up_to_a_minute(self) -> None:
        assert [retry_delay(n) for n in range(8)] == [1, 2, 4, 8, 16, 32, 60, 60]

    def test_a_long_failing_key_stays_at_the_cap(self) -> None:
        assert retry_delay(10_000) == 60
