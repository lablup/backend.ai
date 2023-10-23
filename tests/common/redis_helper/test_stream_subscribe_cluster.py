from __future__ import annotations

import asyncio
import sys
from typing import Dict, List

import aiotools
import pytest
from aiotools.context import aclosing
from redis.asyncio.sentinel import Sentinel

from ai.backend.common import config, redis_helper
from ai.backend.common.types import RedisConnectionInfo

from .types import RedisClusterInfo
from .utils import interrupt, with_timeout


@pytest.mark.redis
@pytest.mark.asyncio
@pytest.mark.parametrize("disruption_method", ["stop", "pause"])
@with_timeout(30.0)
async def test_stream_fanout_cluster(
    redis_cluster: RedisClusterInfo, disruption_method: str, chaos_generator
) -> None:
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

    s = Sentinel(
        redis_cluster.sentinel_addrs,
        password="develove",
        socket_timeout=0.2,
    )

    r = RedisConnectionInfo(
        s.master_for(service_name="mymaster"),
        redis_helper_config=config.redis_helper_default_config,
        sentinel=s,
        name="test",
        service_name="mymaster",
    )

    _execute = aiotools.apartial(redis_helper.execute, r)
    await _execute(lambda r: r.delete("stream1"))

    consumer_tasks = [
        asyncio.create_task(consume("c1", r, "stream1")),
        asyncio.create_task(consume("c2", r, "stream1")),
    ]
    await asyncio.sleep(0.1)
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

    try:
        for i in range(2):
            await _execute(lambda r: r.xadd("stream1", {"idx": i}))
            await asyncio.sleep(0.1)
        do_pause.set()
        await paused.wait()
        loop = asyncio.get_running_loop()
        loop.call_later(2.0, do_unpause.set)
        for i in range(2):
            await _execute(lambda r: r.xadd("stream1", {"idx": 2 + i}))
            await asyncio.sleep(0.1)
        await unpaused.wait()
        for i in range(2):
            await _execute(lambda r: r.xadd("stream1", {"idx": 4 + i}))
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
        assert [*map(int, received_messages["c1"])] == [*range(0, 6)]
        assert [*map(int, received_messages["c2"])] == [*range(0, 6)]
    else:
        # loss happens during failover
        assert {*map(int, received_messages["c1"])} >= {*range(0, 2)} | {*range(4, 6)}
        assert {*map(int, received_messages["c2"])} >= {*range(0, 2)} | {*range(4, 6)}
