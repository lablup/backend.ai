from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiotools
import pytest
import redis
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.asyncio.sentinel import MasterNotFoundError, Sentinel, SlaveNotFoundError
from redis.backoff import ExponentialBackoff
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.backend.common import config, redis_helper
from ai.backend.common import validators as tx
from ai.backend.common.types import HostPortPair

from .types import RedisClusterInfo
from .utils import interrupt, with_timeout

if TYPE_CHECKING:
    from typing import Any


@pytest.mark.asyncio
async def test_connect_with_intrinsic_retry(redis_container: tuple[str, HostPortPair]) -> None:
    addr = redis_container[1]
    r = Redis.from_url(
        f"redis://{addr.host}:{addr.port}",
        socket_timeout=10.0,
        retry=Retry(ExponentialBackoff(), 10),
        retry_on_error=[
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
        ],
    )
    await r.ping()


@pytest.mark.asyncio
async def test_connect_with_tenacity_retry(redis_container: tuple[str, HostPortPair]) -> None:
    addr = redis_container[1]
    r = Redis.from_url(
        f"redis://{addr.host}:{addr.port}",
        socket_timeout=10.0,
    )
    async for attempt in AsyncRetrying(
        wait=wait_exponential(multiplier=0.02, min=0.02, max=5.0),
        stop=stop_after_attempt(10),
        retry=retry_if_exception_type((
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
        )),
    ):
        with attempt:
            await r.ping()


@pytest.mark.redis
@pytest.mark.asyncio
async def test_instantiate_redisconninfo() -> None:
    sentinels = "127.0.0.1:26379,127.0.0.1:26380,127.0.0.1:26381"
    r1 = redis_helper.get_redis_object(
        {
            "sentinel": sentinels,
            "service_name": "mymaster",
            "password": "develove",
            "redis_helper_config": config.redis_helper_default_config,
        },
        name="test",
    )

    assert isinstance(r1.client, Redis)
    assert isinstance(r1.sentinel, Sentinel)

    for i in range(3):
        assert r1.sentinel.sentinels[i].connection_pool.connection_kwargs["host"] == "127.0.0.1"
        assert r1.sentinel.sentinels[i].connection_pool.connection_kwargs["port"] == (26379 + i)
        assert r1.sentinel.sentinels[i].connection_pool.connection_kwargs["db"] == 0

    parsed_addresses: Any = tx.DelimiterSeperatedList(tx.HostPortPair).check_and_return(sentinels)
    r2 = redis_helper.get_redis_object(
        {
            "sentinel": parsed_addresses,
            "service_name": "mymaster",
            "password": "develove",
            "redis_helper_config": config.redis_helper_default_config,
        },
        name="test",
    )

    assert isinstance(r2.client, Redis)
    assert isinstance(r2.sentinel, Sentinel)

    for i in range(3):
        assert r2.sentinel.sentinels[i].connection_pool.connection_kwargs["host"] == "127.0.0.1"
        assert r2.sentinel.sentinels[i].connection_pool.connection_kwargs["port"] == (26379 + i)
        assert r2.sentinel.sentinels[i].connection_pool.connection_kwargs["db"] == 0


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

    s = Sentinel(
        redis_cluster.sentinel_addrs,
        password="develove",
        socket_timeout=0.5,
    )
    async with aiotools.TaskGroup() as tg:
        tg.create_task(control_interrupt())
        tg.create_task(
            interrupt(
                "stop",
                redis_cluster.nodes[0],
                do_pause=do_pause,
                do_unpause=do_unpause,
                paused=paused,
                unpaused=unpaused,
                redis_password="develove",
            )
        )
        await asyncio.sleep(0)

        for _ in range(5):
            print(f"CONNECT REPEAT {_}")
            try:
                master_addr = await s.discover_master("mymaster")
                print("MASTER", master_addr)
            except MasterNotFoundError:
                print("MASTER (not found)")
            try:
                slave_addrs = await s.discover_slaves("mymaster")
                print("SLAVE", slave_addrs)
                slave = s.slave_for("mymaster", db=9)
                await slave.ping()
            except SlaveNotFoundError:
                print("SLAVE (not found)")
            await asyncio.sleep(1)
