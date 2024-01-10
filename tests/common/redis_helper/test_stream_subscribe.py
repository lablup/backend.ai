from __future__ import annotations

import asyncio
import sys
from typing import Dict, List, Tuple

import pytest
from aiotools.context import aclosing
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from ai.backend.common import config, redis_helper
from ai.backend.common.types import HostPortPair, RedisConnectionInfo

from .docker import DockerRedisNode
from .utils import interrupt


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
async def test_stream_fanout(
    redis_container: Tuple[str, HostPortPair], disruption_method: str, chaos_generator
) -> None:
    addr = redis_container[1]
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
            async with aclosing(redis_helper.read_stream(r, key)) as agen:
                async for msg_id, msg_data in agen:
                    print(f"XREAD[{consumer_id}]", msg_id, repr(msg_data), file=sys.stderr)
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception as e:
            print("STREAM_FANOUT.CONSUME: unexpected error", repr(e), file=sys.stderr)
            raise

    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.2),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=None,
        name="test",
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await redis_helper.execute(r, lambda r: r.delete("stream1"))

    consumer_tasks = [
        asyncio.create_task(consume("c1", r, "stream1")),
        asyncio.create_task(consume("c2", r, "stream1")),
    ]
    await asyncio.sleep(0.1)
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
        await r.client.xadd("stream1", {"idx": i})
        await asyncio.sleep(0.1)
    do_pause.set()
    await paused.wait()
    loop = asyncio.get_running_loop()
    loop.call_later(2.0, do_unpause.set)
    for i in range(2):
        # The Redis server is dead temporarily...
        if disruption_method == "stop":
            with pytest.raises(RedisConnectionError):
                await r.client.xadd("stream1", {"idx": 2 + i})
        elif disruption_method == "pause":
            with pytest.raises((RedisConnectionError, asyncio.TimeoutError, RedisTimeoutError)):
                await r.client.xadd("stream1", {"idx": 2 + i})
        else:
            raise RuntimeError("should not reach here")
        await asyncio.sleep(0.1)
    await unpaused.wait()
    for i in range(2):
        await r.client.xadd("stream1", {"idx": 4 + i})
        await asyncio.sleep(0.1)

    await interrupt_task
    for t in consumer_tasks:
        t.cancel()
        await t
    for t in consumer_tasks:
        assert t.done()

    if disruption_method == "stop":
        # loss happens
        assert {*map(int, received_messages["c1"])} >= {*range(0, 2)} | {*range(4, 6)}
        assert {*map(int, received_messages["c2"])} >= {*range(0, 2)} | {*range(4, 6)}
    else:
        # loss does not happen
        # pause keeps the TCP connection and the messages are delivered late.
        assert [*map(int, received_messages["c1"])] == [*range(0, 6)]
        assert [*map(int, received_messages["c2"])] == [*range(0, 6)]
