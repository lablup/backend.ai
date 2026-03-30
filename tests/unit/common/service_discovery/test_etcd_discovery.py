import asyncio
import uuid

import pytest

from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
)
from ai.backend.common.service_discovery.service_discovery import (
    MODEL_SERVICE_GROUP,
    HealthStatus,
    ModelServiceMetadata,
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import ServiceDiscoveryType


async def test_etcd_discovery_register(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service_meta=default_service_metadata,
    )
    service = await etcd_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert service == default_service_metadata


async def test_etcd_discovery_heartbeat(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    prev_meta = default_service_metadata.model_copy(deep=True)
    await etcd_discovery.register(
        service_meta=default_service_metadata,
    )
    await etcd_discovery.heartbeat(
        service_meta=default_service_metadata,
    )
    updated_service_meta: ServiceMetadata = await etcd_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert (
        prev_meta.health_status.last_heartbeat < updated_service_meta.health_status.last_heartbeat
    )
    assert prev_meta == updated_service_meta


async def test_etcd_discovery_unregister(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service_meta=default_service_metadata,
    )
    await etcd_discovery.unregister(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    with pytest.raises(ValueError):
        await etcd_discovery.get_service(
            service_group=default_service_metadata.service_group,
            service_id=default_service_metadata.id,
        )


async def test_etcd_discovery_discover_single_service(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service_meta=default_service_metadata,
    )
    services = await etcd_discovery.discover()
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


async def test_etcd_discovery_discover_multiple_services(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    service_group_1 = "test_group_1"
    service_group_2 = "test_group_2"
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await etcd_discovery.register(
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service_meta=service,
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
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service_meta=service,
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
        service_meta=first_service,
    )
    for i in range(5):
        service = make_mock_service_metadata(service_group_1)
        await etcd_discovery.register(
            service_meta=service,
        )

    for i in range(3):
        service = make_mock_service_metadata(service_group_2)
        await etcd_discovery.register(
            service_meta=service,
        )

    service = await etcd_discovery.get_service(
        service_group=service_group_1,
        service_id=first_service.id,
    )
    assert service == first_service


async def test_etcd_discovery_loop_heartbeat(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
) -> None:
    prev_meta = default_service_metadata.model_copy(deep=True)
    loop = ServiceDiscoveryLoop(ServiceDiscoveryType.ETCD, etcd_discovery, default_service_metadata)

    await asyncio.sleep(5)
    updated_service_meta: ServiceMetadata = await etcd_discovery.get_service(
        service_group=default_service_metadata.service_group,
        service_id=default_service_metadata.id,
    )
    assert (
        prev_meta.health_status.last_heartbeat < updated_service_meta.health_status.last_heartbeat
    )
    loop.close()


async def test_etcd_discovery_loop_with_unhealthy_metadata(
    etcd_discovery: ETCDServiceDiscovery,
    default_service_metadata: ServiceMetadata,
    unhealthy_service_metadata: ServiceMetadata,
) -> None:
    await etcd_discovery.register(
        service_meta=unhealthy_service_metadata,
    )

    sd_loop = ServiceDiscoveryLoop(
        ServiceDiscoveryType.ETCD, etcd_discovery, default_service_metadata
    )

    await asyncio.sleep(5)

    with pytest.raises(ValueError):
        await etcd_discovery.get_service(
            service_group=unhealthy_service_metadata.service_group,
            service_id=unhealthy_service_metadata.id,
        )
    sd_loop.close()


def make_mock_model_service_metadata(
    route_id: uuid.UUID | None = None,
    model_service_name: str = "test-model",
    host: str = "10.0.1.50",
    port: int = 8080,
    metrics_path: str = "/metrics",
    labels: dict[str, str] | None = None,
) -> ModelServiceMetadata:
    return ModelServiceMetadata(
        route_id=route_id or uuid.uuid4(),
        model_service_name=model_service_name,
        host=host,
        port=port,
        metrics_path=metrics_path,
        labels=labels or {},
    )


async def test_etcd_sync_model_service_routes_single(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test syncing a single model service route."""
    route = make_mock_model_service_metadata()

    await etcd_discovery.sync_model_service_routes([route])

    # Verify route was registered
    services = await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)
    assert len(services) == 1
    assert services[0].id == route.route_id
    assert services[0].display_name == route.model_service_name
    assert services[0].endpoint.prometheus_address == f"{route.host}:{route.port}"


async def test_etcd_sync_model_service_routes_multiple(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test syncing multiple model service routes."""
    routes = [
        make_mock_model_service_metadata(model_service_name="vllm-0", port=8080),
        make_mock_model_service_metadata(model_service_name="vllm-1", port=8081),
        make_mock_model_service_metadata(model_service_name="tgi-0", port=8082),
    ]

    await etcd_discovery.sync_model_service_routes(routes)

    # Verify all routes were registered
    services = await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)
    assert len(services) == 3
    service_names = {s.display_name for s in services}
    assert service_names == {"vllm-0", "vllm-1", "tgi-0"}


async def test_etcd_sync_model_service_routes_stale_cleanup(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test that stale routes are removed when not included in sync."""
    route_id_1 = uuid.uuid4()
    route_id_2 = uuid.uuid4()
    route_id_3 = uuid.uuid4()

    # First sync with 3 routes
    initial_routes = [
        make_mock_model_service_metadata(route_id=route_id_1, model_service_name="vllm-0"),
        make_mock_model_service_metadata(route_id=route_id_2, model_service_name="vllm-1"),
        make_mock_model_service_metadata(route_id=route_id_3, model_service_name="tgi-0"),
    ]
    await etcd_discovery.sync_model_service_routes(initial_routes)

    services = await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)
    assert len(services) == 3

    # Second sync with only 2 routes (route_id_2 removed)
    updated_routes = [
        make_mock_model_service_metadata(route_id=route_id_1, model_service_name="vllm-0"),
        make_mock_model_service_metadata(route_id=route_id_3, model_service_name="tgi-0"),
    ]
    await etcd_discovery.sync_model_service_routes(updated_routes)

    # Verify stale route was removed
    services = await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)
    assert len(services) == 2
    service_ids = {s.id for s in services}
    assert route_id_1 in service_ids
    assert route_id_2 not in service_ids
    assert route_id_3 in service_ids


async def test_etcd_sync_model_service_routes_update(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test updating existing route with new data."""
    route_id = uuid.uuid4()

    # First sync with initial data
    initial_route = make_mock_model_service_metadata(
        route_id=route_id,
        model_service_name="vllm-0",
        port=8080,
        labels={"version": "v1"},
    )
    await etcd_discovery.sync_model_service_routes([initial_route])

    # Verify initial state
    service = await etcd_discovery.get_service(MODEL_SERVICE_GROUP, route_id)
    assert service.endpoint.port == 8080
    assert service.labels["version"] == "v1"

    # Second sync with updated data
    updated_route = make_mock_model_service_metadata(
        route_id=route_id,
        model_service_name="vllm-0",
        port=9090,
        labels={"version": "v2"},
    )
    await etcd_discovery.sync_model_service_routes([updated_route])

    # Verify update
    service = await etcd_discovery.get_service(MODEL_SERVICE_GROUP, route_id)
    assert service.endpoint.port == 9090
    assert service.labels["version"] == "v2"


async def test_etcd_sync_model_service_routes_empty(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test syncing empty routes list removes all existing routes."""
    # First sync with routes
    routes = [
        make_mock_model_service_metadata(model_service_name="vllm-0"),
        make_mock_model_service_metadata(model_service_name="vllm-1"),
    ]
    await etcd_discovery.sync_model_service_routes(routes)

    services = await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)
    assert len(services) == 2

    # Sync with empty list
    await etcd_discovery.sync_model_service_routes([])

    # Verify all routes removed
    with pytest.raises(ValueError):
        await etcd_discovery.get_service_group(MODEL_SERVICE_GROUP)


async def test_etcd_sync_model_service_routes_with_custom_labels(
    etcd_discovery: ETCDServiceDiscovery,
) -> None:
    """Test that custom labels are preserved and route_id/model_service_name are auto-added."""
    route = make_mock_model_service_metadata(
        model_service_name="vllm-prod",
        labels={
            "deployment_name": "production",
            "runtime_variant": "vllm",
        },
    )

    await etcd_discovery.sync_model_service_routes([route])

    service = await etcd_discovery.get_service(MODEL_SERVICE_GROUP, route.route_id)

    # Verify auto-added labels
    assert "route_id" in service.labels
    assert service.labels["route_id"] == str(route.route_id)
    assert "model_service_name" in service.labels
    assert service.labels["model_service_name"] == route.model_service_name

    # Verify custom labels preserved
    assert service.labels["deployment_name"] == "production"
    assert service.labels["runtime_variant"] == "vllm"
