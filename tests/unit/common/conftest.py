from __future__ import annotations

import random
import secrets
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import pytest

from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisTarget

if TYPE_CHECKING:
    from ai.backend.testutils.bootstrap import RedisContainerFixture

from ai.backend.testutils.bootstrap import (  # noqa: F401
    ETCD_PASSWORD,
    ETCD_USER,
    etcd_container,
    redis_container,
)

pytest_plugins = [
    "ai.backend.testutils.otel",
]


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--skip-test-redis",
        action="store_true",
        default=False,
        help="run Redis tests",
    )


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "redis: mark test as part of Redis test suite")


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    if config.getoption("--skip-test-redis"):
        # auto-skip tests marked with "redis" unless --test-redis option is given.
        do_skip = pytest.mark.skip(
            reason="skipped because no related files are changed",
        )
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(do_skip)


@pytest.fixture
def test_case_ns() -> str:
    return secrets.token_hex(8)


@pytest.fixture
def test_node_id() -> str:
    return f"test-{secrets.token_hex(4)}"


@pytest.fixture
async def test_valkey_stream_mq(
    redis_container: RedisContainerFixture,  # noqa: F811
    test_node_id: str,
) -> AsyncIterator[RedisQueue]:
    hostport_pair: HostPortPairModel = redis_container[1]
    redis_target = RedisTarget(
        addr=hostport_pair.to_legacy(),
        redis_helper_config={
            "socket_timeout": 5.0,
            "socket_connect_timeout": 2.0,
            "reconnect_poll_timeout": 0.3,
        },
    )
    redis_mq = await RedisQueue.create(
        redis_target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_broadcast",
            consume_stream_keys={"events"},
            subscribe_channels={"events_broadcast"},
            group_name=f"test-group-{random.randint(0, 1000)}",
            node_id=test_node_id,
            db=REDIS_STREAM_DB,
        ),
    )
    try:
        yield redis_mq
    finally:
        await redis_mq.close()


@pytest.fixture
def test_ns() -> str:
    return f"test-{secrets.token_hex(8)}"


@pytest.fixture
async def etcd(
    etcd_container: tuple[str, HostPortPairModel],  # noqa: F811
    test_ns: str,
) -> AsyncIterator[AsyncEtcd]:
    async with AsyncEtcd(
        addrs=[etcd_container[1].to_legacy()],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/testing",
            ConfigScopes.NODE: "node/i-test",
        },
        credentials={"user": ETCD_USER, "password": ETCD_PASSWORD},
    ) as etcd:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        yield etcd
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
