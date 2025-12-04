import random
import secrets
import uuid
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_LIVE_DB,
    REDIS_RATE_LIMIT_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
)
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisTarget, ValkeyTarget
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    redis_container,
    sync_file_lock,
)


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--skip-test-redis",
        action="store_true",
        default=False,
        help="run Redis tests",
    )


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "redis: mark test as part of Redis test suite")


def pytest_collection_modifyitems(config, items) -> None:
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
async def test_valkey_live(redis_container) -> AsyncIterator[ValkeyLiveClient]:  # noqa: F811
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyLiveClient.create(
        valkey_target,
        human_readable_name="test.live",
        db_id=REDIS_LIVE_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_stream(redis_container) -> AsyncIterator[ValkeyStreamClient]:  # noqa: F811
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyStreamClient.create(
        valkey_target,
        human_readable_name="event_producer.stream",
        db_id=REDIS_STREAM_DB,
        pubsub_channels={"test-broadcast"},
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_stat(redis_container) -> AsyncIterator[ValkeyStatClient]:  # noqa: F811
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyStatClient.create(
        valkey_target,
        human_readable_name="test.stat",
        db_id=REDIS_STATISTICS_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_rate_limit(redis_container) -> AsyncIterator[ValkeyRateLimitClient]:  # noqa: F811
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyRateLimitClient.create(
        valkey_target,
        human_readable_name="test.rate_limit",
        db_id=REDIS_RATE_LIMIT_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_artifact(
    redis_container,  # noqa: F811
) -> AsyncIterator[ValkeyArtifactDownloadTrackingClient]:
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    client = await ValkeyArtifactDownloadTrackingClient.create(
        valkey_target,
        human_readable_name="test.artifact",
        db_id=REDIS_STATISTICS_DB,
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def test_valkey_stream_mq(redis_container, test_node_id) -> AsyncIterator[RedisQueue]:  # noqa: F811
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
async def gateway_etcd(etcd_container, test_ns) -> AsyncIterator[AsyncEtcd]:  # noqa: F811
    etcd = AsyncEtcd(
        addrs=[etcd_container[1]],
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
def allow_and_block_list() -> tuple[set[str], ...]:
    return {"cuda"}, {"cuda_mock"}


@pytest.fixture
def allow_and_block_list_has_union() -> tuple[set[str], ...]:
    return {"cuda"}, {"cuda"}


@pytest.fixture
def mock_authenticated_request() -> MagicMock:
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
