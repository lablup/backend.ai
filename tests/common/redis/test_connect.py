from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aioredis
import aioredis.client
import aioredis.exceptions
import aioredis.sentinel
import aiotools
import pytest

from .types import RedisClusterInfo
from .utils import interrupt, with_timeout

from ai.backend.common import redis, validators as tx

if TYPE_CHECKING:
    from typing import Any


@pytest.mark.asyncio
async def test_connect(redis_container: str) -> None:
    r = aioredis.from_url(
        url='redis://localhost:9379',
        socket_timeout=0.5,
    )
    await r.ping()


@pytest.mark.redis
@pytest.mark.asyncio
async def test_instantiate_redisconninfo() -> None:
    sentinels = '127.0.0.1:26379,127.0.0.1:26380,127.0.0.1:26381'
    r1 = redis.get_redis_object({
        'sentinel': sentinels,
        'service_name': 'mymaster',
        'password': 'develove',
    })

    assert isinstance(r1.client, aioredis.sentinel.Sentinel)

    for i in range(3):
        assert r1.client.sentinels[i].connection_pool.connection_kwargs['host'] == '127.0.0.1'
        assert r1.client.sentinels[i].connection_pool.connection_kwargs['port'] == (26379 + i)
        assert r1.client.sentinels[i].connection_pool.connection_kwargs['db'] == 0

    parsed_addresses: Any = tx.DelimiterSeperatedList(tx.HostPortPair).check_and_return(sentinels)
    r2 = redis.get_redis_object({
        'sentinel': parsed_addresses,
        'service_name': 'mymaster',
        'password': 'develove',
    })

    assert isinstance(r2.client, aioredis.sentinel.Sentinel)

    for i in range(3):
        assert r2.client.sentinels[i].connection_pool.connection_kwargs['host'] == '127.0.0.1'
        assert r2.client.sentinels[i].connection_pool.connection_kwargs['port'] == (26379 + i)
        assert r2.client.sentinels[i].connection_pool.connection_kwargs['db'] == 0


@pytest.mark.redis
@pytest.mark.asyncio
@with_timeout(30.0)
async def test_connect_cluster_sentinel(redis_cluster: RedisClusterInfo) -> None:
    do_pause = asyncio.Event()
    paused = asyncio.Event()
    do_unpause = asyncio.Event()
    unpaused = asyncio.Event()

    async def control_interrupt() -> None:
        await asyncio.sleep(1)
        do_pause.set()
        await paused.wait()
        await asyncio.sleep(2)
        do_unpause.set()
        await unpaused.wait()

    s = aioredis.sentinel.Sentinel(
        redis_cluster.sentinel_addrs,
        password='develove',
        socket_timeout=0.5,
    )
    async with aiotools.TaskGroup() as tg:
        tg.create_task(control_interrupt())
        tg.create_task(interrupt(
            'stop',
            redis_cluster.nodes[0],
            do_pause=do_pause,
            do_unpause=do_unpause,
            paused=paused,
            unpaused=unpaused,
            redis_password='develove',
        ))
        await asyncio.sleep(0)

        for _ in range(5):
            print(f"CONNECT REPEAT {_}")
            try:
                master_addr = await s.discover_master('mymaster')
                print("MASTER", master_addr)
            except aioredis.sentinel.MasterNotFoundError:
                print("MASTER (not found)")
            try:
                slave_addrs = await s.discover_slaves('mymaster')
                print("SLAVE", slave_addrs)
                slave = s.slave_for('mymaster', db=9)
                await slave.ping()
            except aioredis.sentinel.SlaveNotFoundError:
                print("SLAVE (not found)")
            await asyncio.sleep(1)
