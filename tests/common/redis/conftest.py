from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest

from .docker import DockerComposeRedisSentinelCluster
from .types import RedisClusterInfo
from .utils import wait_redis_ready

# from .native import NativeRedisSentinelCluster  # unused now
# A simple "redis_container" fixture is defined in ai.backend.testutils.bootstrap.


@pytest.fixture
async def redis_cluster(test_ns, test_case_ns) -> AsyncIterator[RedisClusterInfo]:
    impl = DockerComposeRedisSentinelCluster
    cluster = impl(test_ns, test_case_ns, password="develove", service_name="mymaster")
    async with cluster.make_cluster() as info:
        async with asyncio.TaskGroup() as tg:
            for host, port in info.node_addrs:
                tg.create_task(wait_redis_ready(host, port, "develove"))
            for host, port in info.sentinel_addrs:
                tg.create_task(wait_redis_ready(host, port, None))
        # Give the nodes a grace period to sync up.
        # This is important to reduce intermittent failure of tests.
        await asyncio.sleep(0.3)
        yield info
