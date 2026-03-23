from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.sync import SyncWorkerThread
from ai.backend.common.types import Sentinel


class TestSyncWorkerThread:
    """Tests for the SyncWorkerThread class."""

    def test_execute_coroutine(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        try:

            async def add(a: int, b: int) -> int:
                return a + b

            result = thread.execute(add(3, 4))
            assert result == 7
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_execute_propagates_exception(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        try:

            async def fail() -> None:
                raise ValueError("test error")

            with pytest.raises(ValueError, match="test error"):
                thread.execute(fail())
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_execute_generator(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        try:

            async def gen_items() -> AsyncIterator[int]:
                for i in range(5):
                    yield i

            items = list(thread.execute_generator(gen_items()))
            assert items == [0, 1, 2, 3, 4]
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_execute_generator_with_exception(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        try:

            async def failing_gen() -> AsyncIterator[int]:
                yield 1
                raise RuntimeError("gen error")

            with pytest.raises(RuntimeError, match="gen error"):
                list(thread.execute_generator(failing_gen()))
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_interrupt_generator(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        try:

            async def infinite_gen() -> AsyncIterator[int]:
                i = 0
                while True:
                    yield i
                    i += 1
                    await asyncio.sleep(0)

            items: list[int] = []
            for item in thread.execute_generator(infinite_gen()):
                items.append(item)
                if item >= 2:
                    thread.interrupt_generator()
                    break

            assert items == [0, 1, 2]
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_loop_property(self) -> None:
        thread = SyncWorkerThread()
        assert thread.loop is None
        thread.start()
        try:
            # Execute something to ensure the loop is running
            async def noop() -> None:
                pass

            thread.execute(noop())
            assert thread.loop is not None
        finally:
            thread.work_queue.put(Sentinel.TOKEN)
            thread.join(timeout=5)

    def test_thread_stops_on_sentinel(self) -> None:
        thread = SyncWorkerThread()
        thread.start()
        thread.work_queue.put(Sentinel.TOKEN)
        thread.join(timeout=5)
        assert not thread.is_alive()
