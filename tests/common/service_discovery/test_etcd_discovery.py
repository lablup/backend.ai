import uuid

import pytest

from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
)
from ai.backend.common.service_discovery.service_discovery import (
    HealthStatus,
    ServiceEndpoint,
    ServiceMetadata,
)


async def test_etcd_discovery_register(
    etcd_discovery: ETCDServiceDiscovery,
    default_etcd_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service=default_etcd_metadata,
    )
    service = await etcd_discovery.get_service(
        service_group=default_etcd_metadata.service_group,
        service_id=default_etcd_metadata.id,
    )
    assert service == default_etcd_metadata


async def test_etcd_discovery_heartbeat(
    etcd_discovery: ETCDServiceDiscovery,
    default_etcd_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service=default_etcd_metadata,
    )
    await etcd_discovery.heartbeat(
        service_group=default_etcd_metadata.service_group,
        service_id=default_etcd_metadata.id,
    )
    updated_service_meta: ServiceMetadata = await etcd_discovery.get_service(
        service_group=default_etcd_metadata.service_group,
        service_id=default_etcd_metadata.id,
    )
    assert (
        default_etcd_metadata.health_status.last_heartbeat
        < updated_service_meta.health_status.last_heartbeat
    )
    assert default_etcd_metadata == updated_service_meta


async def test_etcd_discovery_unregister(
    etcd_discovery: ETCDServiceDiscovery,
    default_etcd_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service=default_etcd_metadata,
    )
    await etcd_discovery.unregister(
        service_group=default_etcd_metadata.service_group,
        service_id=default_etcd_metadata.id,
    )
    with pytest.raises(ValueError):
        await etcd_discovery.get_service(
            service_group=default_etcd_metadata.service_group,
            service_id=default_etcd_metadata.id,
        )


async def test_etcd_discovery_discover_single_service(
    etcd_discovery: ETCDServiceDiscovery,
    default_etcd_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service=default_etcd_metadata,
    )
    services = await etcd_discovery.discover()
    assert len(services) == 1
    assert services[0] == default_etcd_metadata


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


async def test_etcd_discovery_discover_multiple_services(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await etcd_discovery.register(
            service=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service=service,
        )

    services = await etcd_discovery.discover()
    assert len(services) == 8
    assert len(list(filter(lambda s: s.service_group == service_group_1, services))) == 5
    assert len(list(filter(lambda s: s.service_group == service_group_2, services))) == 3


async def test_etcd_discovery_get_service_group(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await etcd_discovery.register(
            service=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service=service,
        )

    services = await etcd_discovery.get_service_group(service_group_1)
    assert len(services) == 5

    services = await etcd_discovery.get_service_group(service_group_2)
    assert len(services) == 3


async def test_etcd_discovery_get_service_when_multiple_services(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    first_service = make_mock_service_metadata(service_group_1)
    await etcd_discovery.register(
        service=first_service,
    )
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await etcd_discovery.register(
            service=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service=service,
        )

    service = await etcd_discovery.get_service(
        service_group=service_group_1,
        service_id=first_service.id,
    )
    assert service == first_service
