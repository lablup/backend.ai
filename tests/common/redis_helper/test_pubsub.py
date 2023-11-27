from __future__ import annotations

import asyncio
from typing import List, Tuple

import aiotools
import pytest
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
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
async def test_pubsub(redis_container: Tuple[str, HostPortPair], disruption_method: str) -> None:
    addr = redis_container[1]
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def subscribe(pubsub: PubSub) -> None:
        try:
            async with aiotools.aclosing(
                redis_helper.subscribe(pubsub),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.5),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=None,
        name="test",
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await r.client.delete("ch1")
    pubsub = r.client.pubsub()
    async with pubsub:
        await pubsub.subscribe("ch1")

        subscribe_task = asyncio.create_task(subscribe(pubsub))
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
            await r.client.publish("ch1", str(i))
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()
        for i in range(5):
            # The Redis server is dead temporarily...
            if disruption_method == "stop":
                with pytest.raises(RedisConnectionError):
                    await r.client.publish("ch1", str(5 + i))
            elif disruption_method == "pause":
                with pytest.raises((asyncio.TimeoutError, RedisTimeoutError)):
                    await r.client.publish("ch1", str(5 + i))
            else:
                raise RuntimeError("should not reach here")
            await asyncio.sleep(0.1)
        do_unpause.set()
        await unpaused.wait()
        for i in range(5):
            await r.client.publish("ch1", str(10 + i))
            await asyncio.sleep(0.1)

        await interrupt_task
        subscribe_task.cancel()
        await subscribe_task
        assert subscribe_task.done()

    if disruption_method == "stop":
        all_messages = set(map(int, received_messages))
        assert set(range(0, 5)) <= all_messages
        assert set(range(13, 15)) <= all_messages  # more msgs may be lost during restart
        assert all_messages <= set(range(0, 15))
    elif disruption_method == "pause":
        # Temporary pause of the container makes the kernel TCP stack to keep the packets.
        assert [*map(int, received_messages)] == [*range(0, 15)]
    else:
        raise RuntimeError("should not reach here")


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.xfail
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
async def test_pubsub_with_retrying_pub(
    redis_container: Tuple[str, HostPortPair], disruption_method: str
) -> None:
    addr = redis_container[1]
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def subscribe(pubsub: PubSub) -> None:
        try:
            async with aiotools.aclosing(
                redis_helper.subscribe(pubsub, reconnect_poll_interval=0.3),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.5),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=None,
        name="test",
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await r.client.delete("ch1")
    pubsub = r.client.pubsub()
    async with pubsub:
        await pubsub.subscribe("ch1")

        subscribe_task = asyncio.create_task(subscribe(pubsub))
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
            await redis_helper.execute(r, lambda r: r.publish("ch1", str(i)))
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()

        async def wakeup():
            await asyncio.sleep(0.3)
            do_unpause.set()

        wakeup_task = asyncio.create_task(wakeup())
        for i in range(5):
            await redis_helper.execute(r, lambda r: r.publish("ch1", str(5 + i)))
            await asyncio.sleep(0.1)
        await wakeup_task

        await unpaused.wait()
        for i in range(5):
            await redis_helper.execute(r, lambda r: r.publish("ch1", str(10 + i)))
            await asyncio.sleep(0.1)

        await interrupt_task
        subscribe_task.cancel()
        await subscribe_task
        assert subscribe_task.done()

    all_messages = set(map(int, received_messages))
    assert set(range(0, 5)) <= all_messages
    assert set(range(13, 15)) <= all_messages  # more msgs may be lost during restart
    assert all_messages <= set(range(0, 15))


# FIXME: The below test case hangs...
#        We skipped this issue because now we use Redis streams instead of pub-sub.
r"""
@pytest.mark.redis
@pytest.mark.asyncio
async def test_pubsub_cluster_sentinel(redis_cluster: RedisClusterInfo) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()
    received_messages: List[str] = []

    async def interrupt() -> None:
        await do_pause.wait()
        await simple_run_cmd(['docker', 'stop', redis_container])
        paused.set()
        await do_unpause.wait()
        await simple_run_cmd(['docker', 'start', redis_container])
        # The pub-sub channel may loose some messages while starting up.
        # Make a pause here to wait until the container actually begins to listen.
        await asyncio.sleep(0.5)
        unpaused.set()

    async def subscribe(pubsub: Pubsub) -> None:
        try:
            async with aiotools.aclosing(
                redis.subscribe(pubsub, reconnect_poll_interval=0.3)
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    print("SUBSCRIBE", msg)
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

    s = Sentinel(
        redis_cluster.sentinel_addrs,
        password='develove',
        socket_timeout=0.5,
    )
    await redis.execute(s, lambda r: r.delete("ch1"), service_name="mymaster")

    m = s.master_for("mymaster")
    pubsub = m.pubsub()
    async with pubsub:
        await pubsub.subscribe("ch1")

        subscribe_task = asyncio.create_task(subscribe(pubsub))
        interrupt_task = asyncio.create_task(interrupt())
        await asyncio.sleep(0)

        for i in range(5):
            await redis.execute(s, lambda r: r.publish("ch1", str(i)), service_name="mymaster")
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()

        async def wakeup():
            await asyncio.sleep(2.0)
            do_unpause.set()

        wakeup_task = asyncio.create_task(wakeup())
        for i in range(5):
            await redis.execute(s, lambda r: r.publish("ch1", str(5 + i)), service_name="mymaster")
            await asyncio.sleep(0.1)
        await wakeup_task

        await unpaused.wait()
        for i in range(5):
            await redis.execute(s, lambda r: r.publish("ch1", str(10 + i)), service_name="mymaster")
            await asyncio.sleep(0.1)

        await interrupt_task
        subscribe_task.cancel()
        await subscribe_task
        assert subscribe_task.done()

    assert [*map(int, received_messages)] == [*range(0, 15)]
"""
