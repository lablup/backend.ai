import time
import uuid
from collections.abc import AsyncIterator

import pytest

from ai.backend.common import redis_helper
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    HealthStatus,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    RedisConnectionInfo,
    RedisHelperConfig,
    RedisTarget,
    ValkeyTarget,
)


@pytest.fixture
async def etcd_discovery(etcd: AsyncEtcd) -> AsyncIterator[ETCDServiceDiscovery]:
    prefix = "/ai/backend/test/service_discovery"
    yield ETCDServiceDiscovery(
        args=ETCDServiceDiscoveryArgs(
            etcd=etcd,
            prefix=prefix,
        ),
    )
    # Cleanup
    await etcd.delete_prefix(prefix)


@pytest.fixture
async def redis_conn(redis_container) -> AsyncIterator[RedisConnectionInfo]:
    # Configure test Redis connection
    conn = redis_helper.get_redis_object(
        RedisTarget(
            addr=redis_container[1],
            redis_helper_config=RedisHelperConfig(
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                reconnect_poll_timeout=1.0,
                max_connections=10,
                connection_ready_timeout=1.0,
            ),
        ),
        name="test-redis",
    )
    yield conn
    # Cleanup after tests
    await conn.client.flushdb()
    await conn.close()


@pytest.fixture
async def redis_discovery(redis_container) -> AsyncIterator[RedisServiceDiscovery]:
    # Create a proper RedisTarget for the service discovery
    hostport_pair: HostPortPairModel = redis_container[1]
    valkey_target = ValkeyTarget(
        addr=hostport_pair.address,
    )
    discovery = await RedisServiceDiscovery.create(
        args=RedisServiceDiscoveryArgs(
            valkey_target=valkey_target,
        ),
    )
    try:
        # Flush the database to ensure clean state
        await discovery._valkey_client._client.client.flushdb()
        yield discovery
    finally:
        # Cleanup: flush database before closing
        await discovery._valkey_client._client.client.flushdb()
        await discovery.close()


@pytest.fixture
async def default_service_metadata() -> AsyncIterator[ServiceMetadata]:
    yield ServiceMetadata(
        id=uuid.uuid4(),
        display_name="test_service",
        service_group="test_group",
        version="1.0.0",
        endpoint=ServiceEndpoint(
            address="localhost",
            port=8080,
            protocol="http",
            prometheus_address="localhost:9090",
        ),
        health_status=HealthStatus(),
    )


@pytest.fixture
async def unhealthy_service_metadata() -> AsyncIterator[ServiceMetadata]:
    before_10_minutes = time.time() - 60 * 10
    print(f"Unhealthy service metadata: {before_10_minutes}")
    yield ServiceMetadata(
        id=uuid.uuid4(),
        display_name="test_service",
        service_group="test_group",
        version="1.0.0",
        endpoint=ServiceEndpoint(
            address="localhost",
            port=8080,
            protocol="http",
            prometheus_address="localhost:9090",
        ),
        health_status=HealthStatus(
            registration_time=before_10_minutes,
            last_heartbeat=before_10_minutes,
        ),
    )
