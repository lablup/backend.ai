"""
A compatibility module for backported codes from Python 3.6+ standard library.
"""

import asyncio

__all__ = (
    "current_loop",
    "all_tasks",
    "asyncio_run",
    "asyncio_run_forever",
)


if hasattr(asyncio, "get_running_loop"):  # Python 3.7+
    current_loop = asyncio.get_running_loop
else:
    current_loop = asyncio.get_event_loop


if hasattr(asyncio, "all_tasks"):  # Python 3.7+
    all_tasks = asyncio.all_tasks
else:
    all_tasks = asyncio.Task.all_tasks  # type: ignore


def _cancel_all_tasks(loop):
    to_cancel = all_tasks(loop)
    if not to_cancel:
        return
    for task in to_cancel:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))
    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                "message": "unhandled exception during asyncio.run() shutdown",
                "exception": task.exception(),
                "task": task,
            })


def _asyncio_run(coro, *, debug=False):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(debug)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            _cancel_all_tasks(loop)
            if hasattr(loop, "shutdown_asyncgens"):  # Python 3.6+
                loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.stop()
            loop.close()
            asyncio.set_event_loop(None)


if hasattr(asyncio, "run"):  # Python 3.7+
    asyncio_run = asyncio.run
else:
    asyncio_run = _asyncio_run  # type: ignore[assignment]


def asyncio_run_forever(server_context, *, debug=False):
    """
    A proposed-but-not-implemented asyncio.run_forever() API based on
    @vxgmichel's idea.
    See discussions on https://github.com/python/asyncio/pull/465
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_debug(debug)

    forever = loop.create_future()

    async def _run_forever():
        async with server_context:
            try:
                await forever
            except asyncio.CancelledError:
                pass

    try:
        return loop.run_until_complete(_run_forever())
    finally:
        try:
            _cancel_all_tasks(loop)
            if hasattr(loop, "shutdown_asyncgens"):  # Python 3.6+
                loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.stop()
            loop.close()
            asyncio.set_event_loop(None)
