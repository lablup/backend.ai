from __future__ import annotations

import asyncio
import inspect
import queue
import threading
from collections.abc import AsyncGenerator, AsyncIterator, Coroutine, Iterator
from contextvars import Context, copy_context
from typing import Any, TypeVar, cast

from ai.backend.common.types import Sentinel

_Item = TypeVar("_Item")


class SyncWorkerThread(threading.Thread):
    """
    A worker thread that runs an asyncio event loop internally,
    allowing synchronous code to execute coroutines and async generators.

    Extracted from the client SDK's Session class for reuse
    across sync wrappers (e.g., SyncClientPool).
    """

    work_queue: queue.Queue[
        tuple[AsyncIterator[Any] | Coroutine[Any, Any, Any], Context] | Sentinel
    ]
    done_queue: queue.Queue[Any | Exception]
    stream_queue: queue.Queue[Any | Exception | Sentinel]
    stream_block: threading.Event
    agen_shutdown: bool
    _loop: asyncio.AbstractEventLoop | None
    _loop_ready: threading.Event

    __slots__ = (
        "_loop",
        "_loop_ready",
        "agen_shutdown",
        "done_queue",
        "stream_block",
        "stream_queue",
        "work_queue",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()
        self.stream_queue = queue.Queue()
        self.stream_block = threading.Event()
        self.agen_shutdown = False
        self._loop = None
        self._loop_ready = threading.Event()

    @property
    def loop(self) -> asyncio.AbstractEventLoop | None:
        """The event loop running inside this worker thread (available after start)."""
        return self._loop

    def wait_until_ready(self, timeout: float | None = None) -> None:
        """Block until the worker thread's event loop is ready."""
        self._loop_ready.wait(timeout=timeout)

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._loop_ready.set()
        try:
            while True:
                item = self.work_queue.get()
                if item is Sentinel.TOKEN:
                    break
                coro, ctx = item
                if inspect.isasyncgen(coro):
                    ctx.run(loop.run_until_complete, self.agen_wrapper(coro))
                else:
                    try:
                        result: Any = ctx.run(
                            loop.run_until_complete,
                            cast(Coroutine[Any, Any, Any], coro),
                        )
                    except Exception as e:
                        self.done_queue.put_nowait(e)
                    else:
                        self.done_queue.put_nowait(result)
                self.work_queue.task_done()
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.stop()
            loop.close()
            self._loop = None

    def execute(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Submit a coroutine for execution and block until the result is ready."""
        ctx = copy_context()
        try:
            self.work_queue.put((coro, ctx))
            result = self.done_queue.get()
            self.done_queue.task_done()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            del ctx

    async def agen_wrapper(self, agen: AsyncGenerator[Any, None]) -> None:
        self.agen_shutdown = False
        try:
            async for item in agen:
                self.stream_block.clear()
                self.stream_queue.put(item)
                # flow-control the generator
                self.stream_block.wait()
                if self.agen_shutdown:
                    break
        except Exception as e:
            self.stream_queue.put(e)
        finally:
            self.stream_queue.put(Sentinel.TOKEN)
            await agen.aclose()

    def execute_generator(self, asyncgen: AsyncIterator[_Item]) -> Iterator[_Item]:
        """Submit an async generator and yield items synchronously."""
        ctx = copy_context()
        try:
            self.work_queue.put((asyncgen, ctx))
            while True:
                item = self.stream_queue.get()
                try:
                    if item is Sentinel.TOKEN:
                        break
                    if isinstance(item, Exception):
                        raise item
                    yield item
                finally:
                    self.stream_block.set()
                    self.stream_queue.task_done()
        finally:
            del ctx

    def interrupt_generator(self) -> None:
        """Signal an in-progress async generator to stop."""
        self.agen_shutdown = True
        self.stream_block.set()
        self.stream_queue.put(Sentinel.TOKEN)
