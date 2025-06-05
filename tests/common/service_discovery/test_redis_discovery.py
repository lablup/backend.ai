import asyncio
import uuid

import pytest

from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
)
from ai.backend.common.service_discovery.service_discovery import (
    HealthStatus,
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)


async def test_redis_discovery_register(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await redis_discovery.register(
        service_meta=default_service_metadata,
    )
    service = await redis_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert service == default_service_metadata


async def test_redis_discovery_heartbeat(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    prev_meta = default_service_metadata.model_copy(deep=True)
    await redis_discovery.register(
        service_meta=default_service_metadata,
    )
    await redis_discovery.heartbeat(
        service_meta=default_service_metadata,
    )
    updated_service_meta: ServiceMetadata = await redis_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert (
        prev_meta.health_status.last_heartbeat < updated_service_meta.health_status.last_heartbeat
    )
    assert prev_meta == updated_service_meta


async def test_redis_discovery_unregister(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await redis_discovery.register(
        service_meta=default_service_metadata,
    )
    await redis_discovery.unregister(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    with pytest.raises(ValueError):
        await redis_discovery.get_service(
            service_group=default_service_metadata.service_group,
            service_id=default_service_metadata.id,
        )


async def test_redis_discovery_discover_single_service(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await redis_discovery.register(
        service_meta=default_service_metadata,
    )
    services = await redis_discovery.discover()
    assert len(services) == 1
    assert services[0] == default_service_metadata


def make_mock_service_metadata(
    service_group: str,
) -> ServiceMetadata:
    return ServiceMetadata(
        id=uuid.uuid4(),
        display_name="test_service",
        service_group=service_group,
        version="1.0.0",
        endpoint=ServiceEndpoint(
            address="localhost",
            port=8080,
            protocol="http",
            prometheus_address="localhost:9090",
        ),
        health_status=HealthStatus(),
    )


async def test_redis_discovery_discover_multiple_services(
    redis_discovery: RedisServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await redis_discovery.register(
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await redis_discovery.register(
            service_meta=service,
        )

    services = await redis_discovery.discover()
    assert len(services) == 8
    assert len(list(filter(lambda s: s.service_group == service_group_1, services))) == 5
    assert len(list(filter(lambda s: s.service_group == service_group_2, services))) == 3


async def test_redis_discovery_get_service_group(
    redis_discovery: RedisServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await redis_discovery.register(
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await redis_discovery.register(
            service_meta=service,
        )

    services = await redis_discovery.get_service_group(service_group_1)
    assert len(services) == 5

    services = await redis_discovery.get_service_group(service_group_2)
    assert len(services) == 3


async def test_redis_discovery_get_service_when_multiple_services(
    redis_discovery: RedisServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    first_service = make_mock_service_metadata(service_group_1)
    await redis_discovery.register(
        service_meta=first_service,
    )
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await redis_discovery.register(
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await redis_discovery.register(
            service_meta=service,
        )

    service = await redis_discovery.get_service(
        service_group=service_group_1,
        service_id=first_service.id,
    )
    assert service == first_service


async def test_redis_discovery_loop_heartbeat(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    prev_meta = default_service_metadata.model_copy(deep=True)
    loop = ServiceDiscoveryLoop(redis_discovery, default_service_metadata)

    await asyncio.sleep(5)
    updated_service_meta: ServiceMetadata = await redis_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert (
        prev_meta.health_status.last_heartbeat < updated_service_meta.health_status.last_heartbeat
    )
    loop.close()


async def test_redis_discovery_loop_with_unhealthy_metadata(
    redis_discovery: RedisServiceDiscovery,
    default_service_metadata: ServiceMetadata,
    unhealthy_service_metadata: ServiceMetadata,
) -> None:
    await redis_discovery.register(
        service_meta=unhealthy_service_metadata,
    )

    sd_loop = ServiceDiscoveryLoop(redis_discovery, default_service_metadata)

    await asyncio.sleep(5)

    with pytest.raises(ValueError):
        await redis_discovery.get_service(
            service_group=unhealthy_service_metadata.service_group,
            service_id=unhealthy_service_metadata.id,
        )
    sd_loop.close()
