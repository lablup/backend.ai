import asyncio
import inspect
import queue
import threading
from contextvars import Context, copy_context
from typing import Any, AsyncIterator, Coroutine, Iterator, TypeVar

from .types import Sentinel

_Item = TypeVar("_Item")


class SyncWorkerThread(threading.Thread):
    work_queue: queue.Queue[tuple[AsyncIterator | Coroutine, Context] | Sentinel]
    done_queue: queue.Queue[Any | Exception]
    stream_queue: queue.Queue[Any | Exception | Sentinel]
    stream_block: threading.Event
    agen_shutdown: bool

    __slots__ = (
        "work_queue",
        "done_queue",
        "stream_queue",
        "stream_block",
        "agen_shutdown",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()
        self.stream_queue = queue.Queue()
        self.stream_block = threading.Event()
        self.agen_shutdown = False

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
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
                        # FIXME: Once python/mypy#12756 is resolved, remove the type-ignore tag.
                        result = ctx.run(loop.run_until_complete, coro)  # type: ignore
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

    def execute(self, coro: Coroutine) -> Any:
        ctx = copy_context()  # preserve context for the worker thread
        try:
            self.work_queue.put((coro, ctx))
            result = self.done_queue.get()
            self.done_queue.task_done()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            del ctx

    async def agen_wrapper(self, agen):
        self.agen_shutdown = False
        try:
            async for item in agen:
                self.stream_block.clear()
                self.stream_queue.put(item)
                # flow-control the generator.
                self.stream_block.wait()
                if self.agen_shutdown:
                    break
        except Exception as e:
            self.stream_queue.put(e)
        finally:
            self.stream_queue.put(Sentinel.TOKEN)
            await agen.aclose()

    def execute_generator(self, asyncgen: AsyncIterator[_Item]) -> Iterator[_Item]:
        ctx = copy_context()  # preserve context for the worker thread
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

    def interrupt_generator(self):
        self.agen_shutdown = True
        self.stream_block.set()
        self.stream_queue.put(Sentinel.TOKEN)
