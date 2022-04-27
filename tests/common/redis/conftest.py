from __future__ import annotations

import asyncio
import sys
from typing import (
    AsyncIterator,
)

import pytest

from .types import RedisClusterInfo
from .docker import DockerComposeRedisSentinelCluster
from .native import NativeRedisSentinelCluster
from .utils import wait_redis_ready


# A simple "redis_container" fixture is defined in the main conftest.py


@pytest.fixture
async def redis_cluster(test_ns, test_case_ns) -> AsyncIterator[RedisClusterInfo]:
    if sys.platform.startswith("darwin"):
        impl = NativeRedisSentinelCluster
    else:
        impl = DockerComposeRedisSentinelCluster
    cluster = impl(test_ns, test_case_ns, password="develove", service_name="mymaster")
    async with cluster.make_cluster() as info:
        node_wait_tasks = [
            wait_redis_ready(host, port, "develove")
            for host, port in info.node_addrs
        ]
        sentinel_wait_tasks = [
            wait_redis_ready(host, port, None)
            for host, port in info.sentinel_addrs
        ]
        await asyncio.gather(*node_wait_tasks, *sentinel_wait_tasks)
        yield info
