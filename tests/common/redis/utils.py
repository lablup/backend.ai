from __future__ import annotations

import aioredis
import aioredis.exceptions
import async_timeout
import asyncio
import functools
import sys
from typing import (
    Awaitable,
    Callable,
    Final,
    Sequence,
    TYPE_CHECKING,
    TypeVar,
    Union,
)
from typing_extensions import (
    ParamSpec,
)
if TYPE_CHECKING:
    from .types import AbstractRedisNode


disruptions: Final = {
    'stop': {
        'begin': 'stop',
        'end': 'start',
    },
    'pause': {
        'begin': 'pause',
        'end': 'unpause',
    },
}


async def simple_run_cmd(cmdargs: Sequence[Union[str, bytes]], **kwargs) -> asyncio.subprocess.Process:
    p = await asyncio.create_subprocess_exec(*cmdargs, **kwargs)
    await p.wait()
    return p


async def wait_redis_ready(host: str, port: int, password: str = None) -> None:
    r = aioredis.from_url(f"redis://{host}:{port}", password=password, socket_timeout=0.2)
    while True:
        try:
            print("CheckReady.PING", port, file=sys.stderr)
            await r.ping()
            print("CheckReady.PONG", port, file=sys.stderr)
        except aioredis.exceptions.AuthenticationError:
            raise
        except (
            ConnectionResetError,
            aioredis.exceptions.ConnectionError,
        ):
            await asyncio.sleep(0.1)
        except aioredis.exceptions.TimeoutError:
            pass
        else:
            break


async def interrupt(
    disruption_method: str,
    node: AbstractRedisNode,
    *,
    do_pause: asyncio.Event,
    do_unpause: asyncio.Event,
    paused: asyncio.Event,
    unpaused: asyncio.Event,
    redis_password: str = None,
) -> None:
    # Interrupt
    await do_pause.wait()
    print(f"STOPPING {node}", file=sys.stderr)
    if disruption_method == "stop":
        await node.stop(force_kill=True)
    elif disruption_method == "pause":
        await node.pause()
    print(f"STOPPED {node}", file=sys.stderr)
    paused.set()
    # Resume
    await do_unpause.wait()
    print(f"STARTING {node}", file=sys.stderr)
    if disruption_method == "stop":
        await node.start()
    elif disruption_method == "pause":
        await node.unpause()
    await wait_redis_ready(*node.addr, password=redis_password)
    await asyncio.sleep(0.6)
    print(f"STARTED {node}", file=sys.stderr)
    unpaused.set()


_TReturn = TypeVar('_TReturn')
_PInner = ParamSpec('_PInner')


# FIXME: mypy 0.910 does not support PEP-612 (ParamSpec) yet...

def with_timeout(t: float) -> Callable[        # type: ignore
    [Callable[_PInner, Awaitable[_TReturn]]],
    Callable[_PInner, Awaitable[_TReturn]],
]:
    def wrapper(
        corofunc: Callable[_PInner, Awaitable[_TReturn]],  # type: ignore
    ) -> Callable[_PInner, Awaitable[_TReturn]]:           # type: ignore
        @functools.wraps(corofunc)
        async def run(*args: _PInner.args, **kwargs: _PInner.kwargs) -> _TReturn:  # type: ignore
            async with async_timeout.timeout(t):
                return await corofunc(*args, **kwargs)
        return run
    return wrapper
