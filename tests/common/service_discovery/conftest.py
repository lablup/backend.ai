import time
import uuid

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    HealthStatus,
    ServiceEndpoint,
    ServiceMetadata,
)


@pytest.fixture
async def etcd_discovery(etcd: AsyncEtcd):
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
async def default_service_metadata():
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
async def unhealthy_service_metadata():
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
