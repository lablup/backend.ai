from __future__ import annotations

import asyncio
import contextlib
import traceback
from typing import List, Tuple

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from ai.backend.common import config, redis_helper
from ai.backend.common.types import HostPortPair, RedisConnectionInfo

from .docker import DockerRedisNode
from .utils import interrupt


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.xfail
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
async def test_blist(redis_container: tuple[str, HostPortPair], disruption_method: str) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def pop(r: RedisConnectionInfo, key: str) -> None:
        try:
            async with contextlib.aclosing(
                redis_helper.blpop(r, key),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass
        except Exception:
            traceback.print_exc()

    addr = redis_container[1]
    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.2),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=None,
        name="test",
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await r.client.delete("bl1")

    pop_task = asyncio.create_task(pop(r, "bl1"))
    interrupt_task = asyncio.create_task(
        interrupt(
            disruption_method,
            DockerRedisNode("node", addr.port, redis_container[0]),
            do_pause=do_pause,
            do_unpause=do_unpause,
            paused=paused,
            unpaused=unpaused,
        )
    )
    await asyncio.sleep(0)

    for i in range(2):
        print(f"pushing {i} to bl1")
        await r.client.rpush("bl1", str(i))
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()
    for i in range(2):
        # The Redis server is dead temporarily...
        if disruption_method == "stop":
            with pytest.raises(RedisConnectionError):
                await r.client.rpush("bl1", str(2 + i))
        elif disruption_method == "pause":
            with pytest.raises((asyncio.TimeoutError, RedisTimeoutError)):
                await r.client.rpush("bl1", str(2 + i))
        else:
            raise RuntimeError("should not reach here")
        await asyncio.sleep(0.1)
    do_unpause.set()
    await unpaused.wait()
    for i in range(2):
        await r.client.rpush("bl1", str(4 + i))
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    all_messages = set(map(int, received_messages))
    assert set(range(0, 2)) < all_messages
    assert set(range(5, 6)) < all_messages  # more msgs may be lost during restart
    assert all_messages <= set(range(0, 6))


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.xfail
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
async def test_blist_with_retrying_rpush(
    redis_container: Tuple[str, HostPortPair], disruption_method: str
) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def pop(r: RedisConnectionInfo, key: str) -> None:
        try:
            async with contextlib.aclosing(
                redis_helper.blpop(r, key),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    addr = redis_container[1]
    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.2),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=None,
        name="test",
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await r.client.delete("bl1")

    pop_task = asyncio.create_task(pop(r, "bl1"))
    interrupt_task = asyncio.create_task(
        interrupt(
            disruption_method,
            DockerRedisNode("node", addr.port, redis_container[0]),
            do_pause=do_pause,
            do_unpause=do_unpause,
            paused=paused,
            unpaused=unpaused,
        )
    )
    await asyncio.sleep(0)

    for i in range(2):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(i)))
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()

    async def wakeup():
        await asyncio.sleep(2.0)
        do_unpause.set()

    wakeup_task = asyncio.create_task(wakeup())
    for i in range(2):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(2 + i)))
        await asyncio.sleep(0.1)
    await wakeup_task

    await unpaused.wait()
    for i in range(2):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(4 + i)))
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    all_messages = set(map(int, received_messages))
    assert set(range(0, 2)) < all_messages
    assert set(range(5, 6)) < all_messages  # more msgs may be lost during restart
    assert all_messages <= set(range(0, 6))
