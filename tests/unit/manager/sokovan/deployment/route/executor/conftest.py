"""Fixtures for RouteExecutor tests."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentState,
    ReplicaData,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    """Mock DeploymentRepository."""
    repo = AsyncMock()
    repo.get_deployments_by_ids = AsyncMock(return_value=[])
    repo.update_route_sessions = AsyncMock(return_value=None)
    repo.fetch_session_statuses_by_route_ids = AsyncMock(return_value={})
    repo.fetch_route_service_discovery_info = AsyncMock(return_value=[])
    repo.get_scaling_group_cleanup_configs = AsyncMock(return_value={})
    repo.fetch_deployment_context = AsyncMock(return_value=MagicMock())
    return repo


@pytest.fixture
def mock_scheduling_controller() -> AsyncMock:
    """Mock SchedulingController."""
    controller = AsyncMock()
    controller.enqueue_session_from_draft = AsyncMock(return_value=SessionId(uuid4()))
    controller.mark_sessions_for_termination = AsyncMock(return_value=None)
    return controller


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    return MagicMock()


@pytest.fixture
def mock_client_pool() -> MagicMock:
    """Mock ClientPool."""
    return MagicMock()


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    client = AsyncMock()
    client.get_route_health_records_batch = AsyncMock(return_value={})
    client.get_route_health_statuses_batch = AsyncMock(return_value={})
    client.get_route_probe_targets_batch = AsyncMock(return_value={})
    return client


@pytest.fixture
def mock_service_discovery() -> AsyncMock:
    """Mock ServiceDiscovery."""
    discovery = AsyncMock()
    discovery.sync_model_service_routes = AsyncMock(return_value=None)
    return discovery


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    """Mock EventProducer."""
    producer = AsyncMock()
    producer.anycast_event = AsyncMock(return_value=None)
    return producer


@pytest.fixture
def mock_appproxy_client_pool() -> MagicMock:
    """Mock AppProxyClientPool that hands out a single AsyncMock client.

    Tests can introspect ``pool.load_client.return_value.bulk_update_routes``
    (or ``bulk_register_routes`` / ``bulk_unregister_routes``) to assert
    how many calls Manager made and what the payload looked like.
    """
    pool = MagicMock()
    client = AsyncMock()
    client.bulk_update_routes = AsyncMock()
    client.bulk_register_routes = AsyncMock()
    client.bulk_unregister_routes = AsyncMock()
    pool.load_client = MagicMock(return_value=client)
    return pool


@pytest.fixture
def route_executor(
    mock_deployment_repo: AsyncMock,
    mock_scheduling_controller: AsyncMock,
    mock_config_provider: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_schedule: AsyncMock,
    mock_service_discovery: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_appproxy_client_pool: MagicMock,
) -> RouteExecutor:
    """Create RouteExecutor with mocked dependencies."""
    return RouteExecutor(
        deployment_repo=mock_deployment_repo,
        scheduling_controller=mock_scheduling_controller,
        config_provider=mock_config_provider,
        client_pool=mock_client_pool,
        valkey_schedule=mock_valkey_schedule,
        service_discovery=mock_service_discovery,
        event_producer=mock_event_producer,
        appproxy_client_pool=mock_appproxy_client_pool,
    )


# =============================================================================
# DeploymentInfo Fixtures
# =============================================================================


def _create_deployment_info(
    deployment_id: UUID | None = None,
    lifecycle: EndpointLifecycle = EndpointLifecycle.READY,
    resource_group: str = "default",
) -> DeploymentInfo:
    """Create DeploymentInfo for tests."""
    dep_id = deployment_id or uuid4()

    return DeploymentInfo(
        primary_replica_group_id=ReplicaGroupID(uuid4()),
        id=DeploymentID(dep_id),
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group=resource_group,
            created_user=uuid4(),
            session_owner=uuid4(),
            created_at=datetime.now(tzutc()),
            revision_history_limit=10,
        ),
        state=DeploymentState(
            lifecycle=lifecycle,
            scaling_state=ScalingState.STABLE,
            retry_count=0,
        ),
        replica=ReplicaData(
            replica_count=1,
            desired_replica_count=1,
        ),
        network=DeploymentNetworkData(
            open_to_public=False,
            access_token_ids=None,
            url="http://test.endpoint",
            preferred_domain_name=None,
        ),
        options=DeploymentOptions(),
    )


# =============================================================================
# RouteData Fixtures
# =============================================================================


def _create_route_data(
    route_id: UUID | None = None,
    deployment_id: DeploymentID | None = None,
    session_id: SessionId | None = None,
    status: RouteStatus = RouteStatus.PROVISIONING,
    health_status: RouteHealthStatus = RouteHealthStatus.NOT_CHECKED,
    revision_id: DeploymentRevisionID | None = None,
) -> RouteData:
    """Create RouteData for tests."""
    return RouteData(
        route_id=ReplicaID(route_id) if route_id is not None else ReplicaID(uuid4()),
        deployment_id=deployment_id or DeploymentID(uuid4()),
        session_id=session_id,
        status=status,
        health_status=health_status,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
        revision_id=revision_id or DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
    )


@pytest.fixture
def provisioning_route() -> RouteData:
    """Single PROVISIONING route."""
    return _create_route_data(status=RouteStatus.PROVISIONING)


@pytest.fixture
def provisioning_route_with_session() -> RouteData:
    """PROVISIONING route that already has a session."""
    return _create_route_data(
        status=RouteStatus.PROVISIONING,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def provisioning_routes_multiple() -> list[RouteData]:
    """Multiple PROVISIONING routes."""
    endpoint_id = DeploymentID(uuid4())
    return [
        _create_route_data(deployment_id=endpoint_id, status=RouteStatus.PROVISIONING),
        _create_route_data(deployment_id=endpoint_id, status=RouteStatus.PROVISIONING),
    ]


@pytest.fixture
def running_route() -> RouteData:
    """Single RUNNING route."""
    return _create_route_data(
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def running_routes_multiple() -> list[RouteData]:
    """Multiple RUNNING routes."""
    endpoint_id = DeploymentID(uuid4())
    return [
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
    ]


@pytest.fixture
def healthy_route() -> RouteData:
    """Single HEALTHY route."""
    return _create_route_data(
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def healthy_routes_multiple() -> list[RouteData]:
    """Multiple HEALTHY routes."""
    endpoint_id = DeploymentID(uuid4())
    return [
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
    ]


@pytest.fixture
def unhealthy_route() -> RouteData:
    """Single UNHEALTHY route."""
    return _create_route_data(
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.UNHEALTHY,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def terminating_route() -> RouteData:
    """Single TERMINATING route."""
    return _create_route_data(
        status=RouteStatus.TERMINATING,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def terminating_routes_multiple() -> list[RouteData]:
    """Multiple TERMINATING routes."""
    endpoint_id = DeploymentID(uuid4())
    return [
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.TERMINATING,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            deployment_id=endpoint_id,
            status=RouteStatus.TERMINATING,
            session_id=SessionId(uuid4()),
        ),
    ]


@pytest.fixture
def route_without_session() -> RouteData:
    """Route without session assigned."""
    return _create_route_data(
        status=RouteStatus.TERMINATING,
        session_id=None,
    )


# =============================================================================
# Session Status Fixtures
# =============================================================================


@pytest.fixture
def session_status_running() -> MagicMock:
    """RUNNING session status."""
    status = MagicMock()
    status.is_terminal = MagicMock(return_value=False)
    status.value = "RUNNING"
    return status


@pytest.fixture
def session_status_terminated() -> MagicMock:
    """TERMINATED session status."""
    status = MagicMock()
    status.is_terminal = MagicMock(return_value=True)
    status.value = "TERMINATED"
    return status


# =============================================================================
# Cleanup Config Fixtures
# =============================================================================


@pytest.fixture
def cleanup_config_unhealthy_only() -> MagicMock:
    """Cleanup config that targets UNHEALTHY routes."""
    config = MagicMock()
    config.cleanup_target_statuses = [RouteHealthStatus.UNHEALTHY]
    return config


@pytest.fixture
def cleanup_config_unhealthy_and_degraded() -> MagicMock:
    """Cleanup config that targets UNHEALTHY and DEGRADED routes."""
    config = MagicMock()
    config.cleanup_target_statuses = [RouteHealthStatus.UNHEALTHY, RouteHealthStatus.DEGRADED]
    return config
