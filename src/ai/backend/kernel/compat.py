import asyncio
import signal
from typing import (
    Awaitable, Callable, Optional,
    Collection,
    TypeVar,
)

__all__ = (
    'current_loop',
)


current_loop: Callable[[], asyncio.AbstractEventLoop]
if hasattr(asyncio, 'get_running_loop'):
    current_loop = asyncio.get_running_loop  # type: ignore
else:
    current_loop = asyncio.get_event_loop    # type: ignore


all_tasks: Callable[[], Collection[asyncio.Task]]
if hasattr(asyncio, 'all_tasks'):
    all_tasks = asyncio.all_tasks       # type: ignore
else:
    all_tasks = asyncio.Task.all_tasks  # type: ignore


def _cancel_all_tasks(loop):
    to_cancel = all_tasks(loop)
    if not to_cancel:
        return
    for task in to_cancel:
        task.cancel()
    loop.run_until_complete(
        asyncio.gather(*to_cancel, return_exceptions=True))
    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })


def _asyncio_run(coro, *, debug=False):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(debug)
        return loop.run_until_complete(coro)
    finally:
        try:
            _cancel_all_tasks(loop)
            if hasattr(loop, 'shutdown_asyncgens'):  # Python 3.6+
                loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()


_T = TypeVar('_T')

run: Callable[[Awaitable[_T], Optional[bool]], _T]
if hasattr(asyncio, 'run'):
    asyncio_run = asyncio.run   # type: ignore
else:
    asyncio_run = _asyncio_run  # type: ignore


def asyncio_run_forever(setup_coro, shutdown_coro, *,
                        stop_signals={signal.SIGINT}, debug=False):
    '''
    A proposed-but-not-implemented asyncio.run_forever() API based on
    @vxgmichel's idea.
    See discussions on https://github.com/python/asyncio/pull/465
    '''
    async def wait_for_stop():
        loop = current_loop()
        future = loop.create_future()
        for stop_sig in stop_signals:
            loop.add_signal_handler(stop_sig, future.set_result, stop_sig)
        try:
            recv_sig = await future
        finally:
            loop.remove_signal_handler(recv_sig)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(debug)
        loop.run_until_complete(setup_coro)
        loop.run_until_complete(wait_for_stop())
    finally:
        try:
            loop.run_until_complete(shutdown_coro)
            _cancel_all_tasks(loop)
            if hasattr(loop, 'shutdown_asyncgens'):  # Python 3.6+
                loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
