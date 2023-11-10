from __future__ import annotations

import asyncio
import sys
import traceback
from typing import Dict, List, Tuple

import pytest
from aiotools.context import aclosing
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from ai.backend.common import config, redis_helper
from ai.backend.common.types import HostPortPair, RedisConnectionInfo

from .docker import DockerRedisNode
from .utils import interrupt, with_timeout


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
@with_timeout(30.0)
async def test_stream_loadbalance(
    redis_container: Tuple[str, HostPortPair],
    disruption_method: str,
    chaos_generator,
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
        group_name: str,
        consumer_id: str,
        r: RedisConnectionInfo,
        key: str,
    ) -> None:
        try:
            async with aclosing(
                redis_helper.read_stream_by_group(
                    r,
                    key,
                    group_name,
                    consumer_id,
                    autoclaim_idle_timeout=500,
                )
            ) as agen:
                async for msg_id, msg_data in agen:
                    print(f"-> message: {msg_id} {msg_data!r}")
                    received_messages[consumer_id].append(msg_data[b"idx"])
        except asyncio.CancelledError:
            return
        except Exception:
            traceback.print_exc()
            return

    r = RedisConnectionInfo(
        Redis.from_url(url=f"redis://{addr.host}:{addr.port}", socket_timeout=0.2),
        redis_helper_config=config.redis_helper_default_config,
        name="test",
        sentinel=None,
        service_name=None,
    )
    assert isinstance(r.client, Redis)
    await redis_helper.execute(r, lambda r: r.delete("stream1"))
    await redis_helper.execute(
        r, lambda r: r.xgroup_create("stream1", "group1", "$", mkstream=True)
    )

    consumer_tasks = [
        asyncio.create_task(consume("group1", "c1", r, "stream1")),
        asyncio.create_task(consume("group1", "c2", r, "stream1")),
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
    print("RESUME TEST", file=sys.stderr)
    for i in range(2):
        await r.client.xadd("stream1", {"idx": 4 + i})
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
    assert all_messages >= set(range(0, 1)) | set(range(5, 6))
    assert len(all_messages) >= 3
