from __future__ import annotations

import asyncio
import sys
import traceback
from typing import (
    Dict,
    List,
)

import aioredis
import aioredis.client
import aioredis.exceptions
import aioredis.sentinel
import aiotools
from aiotools.context import aclosing
import pytest

from ai.backend.common import redis
from ai.backend.common.types import RedisConnectionInfo

from .docker import DockerRedisNode
from .types import RedisClusterInfo
from .utils import interrupt, with_timeout


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ['stop', 'pause'])
async def test_stream_fanout(redis_container: str, disruption_method: str, chaos_generator) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: Dict[str, List[str]] = {
        "c1": [],
        "c2": [],
    }

    async def consume(
        consumer_id: str,
        r: RedisConnectionInfo,
        key: str,
    ) -> None:
        try:
            async with aclosing(redis.read_stream(r, key)) as agen:
                async for msg_id, msg_data in agen:
                    print(f"XREAD[{consumer_id}]", msg_id, repr(msg_data), file=sys.stderr)
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception as e:
            print("STREAM_FANOUT.CONSUME: unexpected error", repr(e), file=sys.stderr)
            raise

    r = RedisConnectionInfo(
        aioredis.from_url('redis://localhost:9379', socket_timeout=0.5),
        service_name=None,
    )
    assert isinstance(r.client, aioredis.Redis)
    await redis.execute(r, lambda r: r.delete("stream1"))

    consumer_tasks = [
        asyncio.create_task(consume("c1", r, "stream1")),
        asyncio.create_task(consume("c2", r, "stream1")),
    ]
    await asyncio.sleep(0.1)
    interrupt_task = asyncio.create_task(interrupt(
        disruption_method,
        DockerRedisNode("node", 9379, redis_container),
        do_pause=do_pause,
        do_unpause=do_unpause,
        paused=paused,
        unpaused=unpaused,
    ))
    await asyncio.sleep(0)

    for i in range(5):
        await r.client.xadd("stream1", {"idx": i})
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()
    loop = asyncio.get_running_loop()
    loop.call_later(5.0, do_unpause.set)
    for i in range(5):
        # The Redis server is dead temporarily...
        if disruption_method == 'stop':
            with pytest.raises(aioredis.exceptions.ConnectionError):
                await r.client.xadd("stream1", {"idx": 5 + i})
        elif disruption_method == 'pause':
            with pytest.raises(asyncio.TimeoutError):
                await r.client.xadd("stream1", {"idx": 5 + i})
        else:
            raise RuntimeError("should not reach here")
        await asyncio.sleep(0.1)
    await unpaused.wait()
    for i in range(5):
        await r.client.xadd("stream1", {"idx": 10 + i})
        await asyncio.sleep(0.1)

    await interrupt_task
    for t in consumer_tasks:
        t.cancel()
        await t
    for t in consumer_tasks:
        assert t.done()

    if disruption_method == "stop":
        # loss happens
        assert {*map(int, received_messages["c1"])} >= {*range(0, 5)} | {*range(10, 15)}
        assert {*map(int, received_messages["c2"])} >= {*range(0, 5)} | {*range(10, 15)}
    else:
        # loss does not happen
        # pause keeps the TCP connection and the messages are delivered late.
        assert [*map(int, received_messages["c1"])] == [*range(0, 15)]
        assert [*map(int, received_messages["c2"])] == [*range(0, 15)]


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ['stop', 'pause'])
@with_timeout(30.0)
async def test_stream_fanout_cluster(redis_cluster: RedisClusterInfo, disruption_method: str, chaos_generator) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: Dict[str, List[str]] = {
        "c1": [],
        "c2": [],
    }

    async def consume(
        consumer_id: str,
        r: RedisConnectionInfo,
        key: str,
    ) -> None:
        try:
            async with aclosing(redis.read_stream(r, key)) as agen:
                async for msg_id, msg_data in agen:
                    print(f"XREAD[{consumer_id}]", msg_id, repr(msg_data), file=sys.stderr)
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception as e:
            print("STREAM_FANOUT.CONSUME: unexpected error", repr(e), file=sys.stderr)
            raise

    s = RedisConnectionInfo(
        aioredis.sentinel.Sentinel(
            redis_cluster.sentinel_addrs,
            password='develove',
            socket_timeout=0.5,
        ),
        service_name='mymaster',
    )
    _execute = aiotools.apartial(redis.execute, s)
    await _execute(lambda r: r.delete("stream1"))

    consumer_tasks = [
        asyncio.create_task(consume("c1", s, "stream1")),
        asyncio.create_task(consume("c2", s, "stream1")),
    ]
    await asyncio.sleep(0.1)
    interrupt_task = asyncio.create_task(interrupt(
        disruption_method,
        redis_cluster.nodes[0],
        do_pause=do_pause,
        do_unpause=do_unpause,
        paused=paused,
        unpaused=unpaused,
        redis_password='develove',
    ))
    await asyncio.sleep(0)

    try:
        for i in range(5):
            await _execute(lambda r: r.xadd("stream1", {"idx": i}))
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()
        loop = asyncio.get_running_loop()
        loop.call_later(5.0, do_unpause.set)
        for i in range(5):
            await _execute(lambda r: r.xadd("stream1", {"idx": 5 + i}))
            await asyncio.sleep(0.1)
        await unpaused.wait()
        for i in range(5):
            await _execute(lambda r: r.xadd("stream1", {"idx": 10 + i}))
            await asyncio.sleep(0.1)
    finally:
        await interrupt_task
        for t in consumer_tasks:
            t.cancel()
            await t
        for t in consumer_tasks:
            assert t.done()

    if disruption_method == "stop":
        # loss does not happen due to retries
        assert [*map(int, received_messages["c1"])] == [*range(0, 15)]
        assert [*map(int, received_messages["c2"])] == [*range(0, 15)]
    else:
        # loss happens during failover
        assert {*map(int, received_messages["c1"])} >= {*range(0, 5)} | {*range(10, 15)}
        assert {*map(int, received_messages["c2"])} >= {*range(0, 5)} | {*range(10, 15)}


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ['stop', 'pause'])
@with_timeout(30.0)
async def test_stream_loadbalance(redis_container: str, disruption_method: str, chaos_generator) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: Dict[str, List[str]] = {
        "c1": [],
        "c2": [],
    }

    async def consume(
        group_name: str,
        consumer_id: str,
        r: RedisConnectionInfo,
        key: str,
    ) -> None:
        try:
            async with aclosing(redis.read_stream_by_group(
                r, key, group_name, consumer_id,
                autoclaim_idle_timeout=500,
            )) as agen:
                async for msg_id, msg_data in agen:
                    print(f"-> message: {msg_id} {msg_data!r}")
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception:
            traceback.print_exc()
            return

    r = RedisConnectionInfo(
        aioredis.from_url(url='redis://localhost:9379', socket_timeout=0.5),
        service_name=None,
    )
    assert isinstance(r.client, aioredis.Redis)
    await redis.execute(r, lambda r: r.delete("stream1"))
    await redis.execute(r, lambda r: r.xgroup_create("stream1", "group1", b"$", mkstream=True))

    consumer_tasks = [
        asyncio.create_task(consume("group1", "c1", r, "stream1")),
        asyncio.create_task(consume("group1", "c2", r, "stream1")),
    ]
    await asyncio.sleep(0.1)
    interrupt_task = asyncio.create_task(interrupt(
        disruption_method,
        DockerRedisNode("node", 9379, redis_container),
        do_pause=do_pause,
        do_unpause=do_unpause,
        paused=paused,
        unpaused=unpaused,
    ))
    await asyncio.sleep(0)

    for i in range(5):
        await r.client.xadd("stream1", {"idx": i})
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()
    loop = asyncio.get_running_loop()
    loop.call_later(5.0, do_unpause.set)
    for i in range(5):
        # The Redis server is dead temporarily...
        if disruption_method == 'stop':
            with pytest.raises(aioredis.exceptions.ConnectionError):
                await r.client.xadd("stream1", {"idx": 5 + i})
        elif disruption_method == 'pause':
            with pytest.raises(asyncio.TimeoutError):
                await r.client.xadd("stream1", {"idx": 5 + i})
        else:
            raise RuntimeError("should not reach here")
        await asyncio.sleep(0.1)
    await unpaused.wait()
    print("RESUME TEST", file=sys.stderr)
    for i in range(5):
        await r.client.xadd("stream1", {"idx": 10 + i})
        await asyncio.sleep(0.1)
    print("RESUME TEST DONE", file=sys.stderr)

    await interrupt_task
    for t in consumer_tasks:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
    await asyncio.gather(*consumer_tasks, return_exceptions=True)

    # loss happens
    all_messages = set(map(int, received_messages["c1"])) | set(map(int, received_messages["c2"]))
    print(f"{all_messages=}")
    assert all_messages >= set(range(0, 5)) | set(range(10, 15))
    assert len(all_messages) >= 10


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ['stop', 'pause'])
@with_timeout(30.0)
async def test_stream_loadbalance_cluster(redis_cluster: RedisClusterInfo, disruption_method: str, chaos_generator) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: Dict[str, List[str]] = {
        "c1": [],
        "c2": [],
    }

    async def consume(
        group_name: str,
        consumer_id: str,
        r: RedisConnectionInfo,
        key: str,
    ) -> None:
        try:
            async with aclosing(redis.read_stream_by_group(
                r, key, group_name, consumer_id,
                autoclaim_idle_timeout=500,
            )) as agen:
                async for msg_id, msg_data in agen:
                    print(f"-> message: {msg_id} {msg_data!r}")
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception:
            traceback.print_exc()
            return

    s = RedisConnectionInfo(
        aioredis.sentinel.Sentinel(
            redis_cluster.sentinel_addrs,
            password='develove',
            socket_timeout=0.5,
        ),
        service_name='mymaster',
    )
    _execute = aiotools.apartial(redis.execute, s)
    await _execute(lambda r: r.delete("stream1"))
    await _execute(lambda r: r.xgroup_create("stream1", "group1", b"$", mkstream=True))

    consumer_tasks = [
        asyncio.create_task(consume("group1", "c1", s, "stream1")),
        asyncio.create_task(consume("group1", "c2", s, "stream1")),
    ]
    await asyncio.sleep(0.1)
    interrupt_task = asyncio.create_task(interrupt(
        disruption_method,
        redis_cluster.nodes[0],
        do_pause=do_pause,
        do_unpause=do_unpause,
        paused=paused,
        unpaused=unpaused,
        redis_password='develove',
    ))
    await asyncio.sleep(0)

    try:
        for i in range(5):
            await _execute(lambda r: r.xadd("stream1", {"idx": i}))
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()
        loop = asyncio.get_running_loop()
        loop.call_later(5.0, do_unpause.set)
        for i in range(5):
            # The Redis server is dead temporarily...
            await _execute(lambda r: r.xadd("stream1", {"idx": 5 + i}))
            await asyncio.sleep(0.1)
        await unpaused.wait()
        for i in range(5):
            await _execute(lambda r: r.xadd("stream1", {"idx": 10 + i}))
            await asyncio.sleep(0.1)
    finally:
        await interrupt_task
        for t in consumer_tasks:
            t.cancel()
        await asyncio.gather(*consumer_tasks, return_exceptions=True)

    # loss may happen
    all_messages = set(map(int, received_messages["c1"])) | set(map(int, received_messages["c2"]))
    print(f"{all_messages=}")
    assert all_messages >= set(range(0, 5)) | set(range(10, 15))
    assert len(all_messages) >= 10
