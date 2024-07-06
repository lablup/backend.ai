from __future__ import annotations

import asyncio
import socket
from typing import AsyncIterator, cast

import pytest

from .docker import DockerComposeRedisSentinelCluster
from .types import RedisClusterInfo
from .utils import wait_redis_ready

# NOTE: A simple "redis_container" fixture is defined in ai.backend.testutils.bootstrap.


@pytest.fixture(scope="session", autouse=True)
def check_dns_config() -> None:
    # The Redis test suite include clustering failover behavioral test cases
    # which require a special host DNS configuration.
    try:
        assert "127.0.0.1" == socket.gethostbyname("node01")
        assert "127.0.0.1" == socket.gethostbyname("node02")
        assert "127.0.0.1" == socket.gethostbyname("node03")
    except (socket.gaierror, AssertionError):
        pytest.fail(
            "The hostnames node01, node02, node03 should be set to indicate "
            "127.0.0.1 via /etc/hosts"
        )


@pytest.fixture
async def redis_cluster(
    request: pytest.FixtureRequest,
    test_ns: str,
    test_case_ns: str,
) -> AsyncIterator[RedisClusterInfo]:
    impl = DockerComposeRedisSentinelCluster
    verbosity = cast(int, request.config.getoption("--verbose"))
    cluster = impl(
        test_ns,
        test_case_ns,
        password="develove",
        service_name="mymaster",
        verbose=verbosity > 0,
    )
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
