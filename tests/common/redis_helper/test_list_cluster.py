from __future__ import annotations

import asyncio
from typing import List

import aiotools
import pytest
from redis.asyncio.sentinel import Sentinel

from ai.backend.common import config, redis_helper
from ai.backend.common.types import RedisConnectionInfo

from .types import RedisClusterInfo
from .utils import interrupt, with_timeout


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
                    service_name="mymaster",
                ),
            ) as agen:
                async for raw_msg in agen:
                    msg = raw_msg.decode()
                    received_messages.append(msg)
        except asyncio.CancelledError:
            pass

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
    await redis_helper.execute(r, lambda r: r.delete("bl1"))

    pop_task = asyncio.create_task(pop(r, "bl1"))
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

    for i in range(2):
        await redis_helper.execute(
            r,
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
    for i in range(2):
        await redis_helper.execute(
            r,
            lambda r: r.rpush("bl1", str(2 + i)),
            service_name="mymaster",
        )
        await asyncio.sleep(0.1)
    await wakeup_task

    await unpaused.wait()
    for i in range(2):
        await redis_helper.execute(
            r,
            lambda r: r.rpush("bl1", str(4 + i)),
            service_name="mymaster",
        )
        await asyncio.sleep(0.1)

    await interrupt_task
    pop_task.cancel()
    await pop_task
    assert pop_task.done()

    if disruption_method == "stop":
        assert [*map(int, received_messages)] == [*range(0, 6)]
    else:
        # loss happens during failover
        all_messages = set(map(int, received_messages))
        assert set(range(0, 2)) < all_messages
        assert set(range(4, 6)) < all_messages
        assert all_messages <= set(range(0, 6))
