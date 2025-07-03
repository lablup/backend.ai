import asyncio
import random
import secrets
import time
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import RedisTarget
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    redis_container,
    sync_file_lock,
)


def pytest_addoption(parser):
    parser.addoption(
        "--skip-test-redis",
        action="store_true",
        default=False,
        help="run Redis tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "redis: mark test as part of Redis test suite")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-test-redis"):
        # auto-skip tests marked with "redis" unless --test-redis option is given.
        do_skip = pytest.mark.skip(
            reason="skipped because no related files are changed",
        )
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(do_skip)


@pytest.fixture(scope="session", autouse=True)
def test_ns():
    return f"test-{secrets.token_hex(8)}"


@pytest.fixture
def test_case_ns():
    return secrets.token_hex(8)


@pytest.fixture
def test_node_id():
    return f"test-{secrets.token_hex(4)}"


@pytest.fixture
async def etcd(etcd_container, test_ns):  # noqa: F811
    etcd = AsyncEtcd(
        addr=etcd_container[1],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/testing",
            ConfigScopes.NODE: "node/i-test",
        },
    )
    try:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        yield etcd
    finally:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        await etcd.close()
        del etcd


@pytest.fixture
async def test_valkey_stream(redis_container):  # noqa: F811
    redis_target = RedisTarget(
        addr=redis_container[1],
        redis_helper_config={
            "socket_timeout": 5.0,
            "socket_connect_timeout": 2.0,
            "reconnect_poll_timeout": 0.3,
        },
    )
    client = await ValkeyStreamClient.create(
        redis_target,
        name="event_producer.stream",
        db=REDIS_STREAM_DB,
        pubsub_channels=["test-broadcast"],
    )
    yield client


@pytest.fixture
async def test_valkey_stream_mq(redis_container, test_node_id):  # noqa: F811
    redis_target = RedisTarget(
        addr=redis_container[1],
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
            consume_stream_keys=["events"],
            subscribe_channels=["events_broadcast"],
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
async def gateway_etcd(etcd_container, test_ns):  # noqa: F811
    etcd = AsyncEtcd(
        addr=etcd_container[1],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "",
        },
    )
    try:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        yield etcd
    finally:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        del etcd


@pytest.fixture
async def chaos_generator():
    async def _chaos():
        try:
            while True:
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            return

    tasks = []
    for i in range(20):
        tasks.append(asyncio.create_task(_chaos()))
    yield
    for i in range(20):
        tasks[i].cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
def mock_time(mocker):
    total_delay = Decimal(0)
    call_count = 0
    base_time = time.monotonic()
    accum_time = Decimal(0)
    q = Decimal(".000000")

    async def _mock_async_sleep(delay: float) -> None:
        nonlocal total_delay, call_count, accum_time, q
        call_count += 1
        quantized_delay = Decimal(delay).quantize(q)
        accum_time += quantized_delay
        total_delay += quantized_delay

    def _reset() -> None:
        nonlocal total_delay, call_count
        total_delay = Decimal(0)
        call_count = 0

    def _get_total_delay() -> float:
        nonlocal total_delay
        return float(total_delay)

    def _get_call_count() -> int:
        nonlocal call_count
        return call_count

    def _mock_time_monotonic() -> float:
        nonlocal accum_time
        return base_time + float(accum_time)

    _mock_async_sleep.reset = _reset
    _mock_async_sleep.get_total_delay = _get_total_delay
    _mock_async_sleep.get_call_count = _get_call_count
    yield _mock_async_sleep, _mock_time_monotonic


@pytest.fixture
def allow_and_block_list():
    return {"cuda"}, {"cuda_mock"}


@pytest.fixture
def allow_and_block_list_has_union():
    return {"cuda"}, {"cuda"}


@pytest.fixture
def mock_authenticated_request():
    mock_request = MagicMock()
    mock_request["user"] = {
        "uuid": uuid.uuid4(),
        "role": "user",
        "email": "test@email.com",
        "domain_name": "default",
    }
    mock_request["keypair"] = {
        "access_key": "TESTKEY",
        "resource_policy": {"allowed_vfolder_hosts": ["local"]},
    }
    vfolder_id = str(uuid.uuid4())
    mock_request.match_info = {"vfolder_id": vfolder_id}
    return mock_request
