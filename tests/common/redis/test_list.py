from __future__ import annotations

import asyncio
import traceback
from typing import List, Tuple

import aiotools
import pytest
from redis.asyncio import Redis
from redis.asyncio.sentinel import Sentinel
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from ai.backend.common import redis_helper
from ai.backend.common.types import HostPortPair, RedisConnectionInfo

from .docker import DockerRedisNode
from .types import RedisClusterInfo
from .utils import interrupt, with_timeout


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
            async with aiotools.aclosing(
                redis_helper.blpop(r, key, reconnect_poll_interval=0.3),
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
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.5),
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

    for i in range(5):
        print(f"pushing {i} to bl1")
        await r.client.rpush("bl1", str(i))
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()
    for i in range(5):
        # The Redis server is dead temporarily...
        if disruption_method == "stop":
            with pytest.raises(RedisConnectionError):
                await r.client.rpush("bl1", str(5 + i))
        elif disruption_method == "pause":
            with pytest.raises((asyncio.TimeoutError, RedisTimeoutError)):
                await r.client.rpush("bl1", str(5 + i))
        else:
            raise RuntimeError("should not reach here")
        await asyncio.sleep(0.1)
    do_unpause.set()
    await unpaused.wait()
    for i in range(5):
        await r.client.rpush("bl1", str(10 + i))
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    all_messages = set(map(int, received_messages))
    assert set(range(0, 5)) < all_messages
    assert set(range(13, 15)) < all_messages  # more msgs may be lost during restart
    assert all_messages <= set(range(0, 15))


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
            async with aiotools.aclosing(
                redis_helper.blpop(r, key, reconnect_poll_interval=0.3),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    addr = redis_container[1]
    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.5),
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

    for i in range(5):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(i)))
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()

    async def wakeup():
        await asyncio.sleep(2.0)
        do_unpause.set()

    wakeup_task = asyncio.create_task(wakeup())
    for i in range(5):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(5 + i)))
        await asyncio.sleep(0.1)
    await wakeup_task

    await unpaused.wait()
    for i in range(5):
        await redis_helper.execute(r, lambda r: r.rpush("bl1", str(10 + i)))
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    all_messages = set(map(int, received_messages))
    assert set(range(0, 5)) < all_messages
    assert set(range(13, 15)) < all_messages  # more msgs may be lost during restart
    assert all_messages <= set(range(0, 15))


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.xfail
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
@with_timeout(30.0)
async def test_blist_cluster_sentinel(
    redis_cluster: RedisClusterInfo,
    disruption_method: str,
) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def pop(s: RedisConnectionInfo, key: str) -> None:
        try:
            async with aiotools.aclosing(
                redis_helper.blpop(
                    s,
                    key,
                    reconnect_poll_interval=0.3,
                    service_name="mymaster",
                ),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    s = RedisConnectionInfo(
        Sentinel(
            redis_cluster.sentinel_addrs,
            password="develove",
            socket_timeout=0.5,
        ),
        service_name="mymaster",
    )
    await redis_helper.execute(s, lambda r: r.delete("bl1"))

    pop_task = asyncio.create_task(pop(s, "bl1"))
    interrupt_task = asyncio.create_task(
        interrupt(
            disruption_method,
            redis_cluster.nodes[0],
            do_pause=do_pause,
            do_unpause=do_unpause,
            paused=paused,
            unpaused=unpaused,
            redis_password="develove",
        )
    )
    await asyncio.sleep(0)

    for i in range(5):
        await redis_helper.execute(
            s,
            lambda r: r.rpush("bl1", str(i)),
            service_name="mymaster",
        )
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()

    async def wakeup():
        await asyncio.sleep(2.0)
        do_unpause.set()

    wakeup_task = asyncio.create_task(wakeup())
    for i in range(5):
        await redis_helper.execute(
            s,
            lambda r: r.rpush("bl1", str(5 + i)),
            service_name="mymaster",
        )
        await asyncio.sleep(0.1)
    await wakeup_task

    await unpaused.wait()
    for i in range(5):
        await redis_helper.execute(
            s,
            lambda r: r.rpush("bl1", str(10 + i)),
            service_name="mymaster",
        )
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    if disruption_method == "stop":
        assert [*map(int, received_messages)] == [*range(0, 15)]
    else:
        # loss happens during failover
        all_messages = set(map(int, received_messages))
        assert set(range(0, 5)) < all_messages
        assert set(range(10, 15)) < all_messages
        assert all_messages <= set(range(0, 15))
