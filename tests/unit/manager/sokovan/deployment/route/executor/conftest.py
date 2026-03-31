"""Fixtures for RouteExecutor tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    HealthCheckStatus,
    HealthStatus,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
    RouteStatus,
)
from ai.backend.manager.repositories.deployment.types import (
    RouteData,
    RouteServiceDiscoveryInfo,
)
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    """Mock DeploymentRepository."""
    repo = AsyncMock()
    repo.get_endpoints_by_ids = AsyncMock(return_value=[])
    repo.update_route_sessions = AsyncMock(return_value=None)
    repo.fetch_session_statuses_by_route_ids = AsyncMock(return_value={})
    repo.fetch_route_service_discovery_info = AsyncMock(return_value=[])
    repo.get_scaling_group_cleanup_configs = AsyncMock(return_value={})
    repo.fetch_deployment_context = AsyncMock(return_value=MagicMock())
    repo.get_endpoint_health_check_config = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_scheduling_controller() -> AsyncMock:
    """Mock SchedulingController."""
    controller = AsyncMock()
    controller.enqueue_session = AsyncMock(return_value=SessionId(uuid4()))
    controller.mark_sessions_for_termination = AsyncMock(return_value=None)
    return controller


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    provider = MagicMock()
    provider.config.manager.session_schedule_lock_lifetime = 30.0
    return provider


@pytest.fixture
def mock_client_pool() -> MagicMock:
    """Mock ClientPool."""
    return MagicMock()


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    client = AsyncMock()
    client.check_route_health_status = AsyncMock(return_value={})
    client.apply_readiness_check_results = AsyncMock(return_value={})
    return client


@pytest.fixture
def mock_service_discovery() -> AsyncMock:
    """Mock ServiceDiscovery."""
    discovery = AsyncMock()
    discovery.sync_model_service_routes = AsyncMock(return_value=None)
    return discovery


@pytest.fixture
def route_executor(
    mock_deployment_repo: AsyncMock,
    mock_scheduling_controller: AsyncMock,
    mock_config_provider: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_schedule: AsyncMock,
    mock_service_discovery: AsyncMock,
) -> RouteExecutor:
    """Create RouteExecutor with mocked dependencies."""
    return RouteExecutor(
        deployment_repo=mock_deployment_repo,
        scheduling_controller=mock_scheduling_controller,
        config_provider=mock_config_provider,
        client_pool=mock_client_pool,
        valkey_schedule=mock_valkey_schedule,
        service_discovery=mock_service_discovery,
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
        id=dep_id,
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
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=1,
            desired_replica_count=1,
        ),
        network=DeploymentNetworkSpec(
            open_to_public=False,
            url="http://test.endpoint",
        ),
        model_revisions=[],
        current_revision_id=uuid4(),
    )


# =============================================================================
# RouteData Fixtures
# =============================================================================


def _create_route_data(
    route_id: UUID | None = None,
    endpoint_id: UUID | None = None,
    session_id: SessionId | None = None,
    status: RouteStatus = RouteStatus.PROVISIONING,
    revision_id: UUID | None = None,
    created_at: datetime | None = None,
) -> RouteData:
    """Create RouteData for tests."""
    return RouteData(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id or uuid4(),
        session_id=session_id,
        status=status,
        traffic_ratio=1.0,
        created_at=created_at or datetime.now(tzutc()),
        revision_id=revision_id,
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
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.PROVISIONING),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.PROVISIONING),
    ]


@pytest.fixture
def running_route() -> RouteData:
    """Single RUNNING route."""
    return _create_route_data(
        status=RouteStatus.HEALTHY,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def running_routes_multiple() -> list[RouteData]:
    """Multiple RUNNING routes."""
    endpoint_id = uuid4()
    return [
        _create_route_data(
            endpoint_id=endpoint_id,
            status=RouteStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            endpoint_id=endpoint_id,
            status=RouteStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
    ]


@pytest.fixture
def healthy_route() -> RouteData:
    """Single HEALTHY route."""
    return _create_route_data(
        status=RouteStatus.HEALTHY,
        session_id=SessionId(uuid4()),
    )


@pytest.fixture
def healthy_routes_multiple() -> list[RouteData]:
    """Multiple HEALTHY routes."""
    endpoint_id = uuid4()
    return [
        _create_route_data(
            endpoint_id=endpoint_id,
            status=RouteStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            endpoint_id=endpoint_id,
            status=RouteStatus.HEALTHY,
            session_id=SessionId(uuid4()),
        ),
    ]


@pytest.fixture
def unhealthy_route() -> RouteData:
    """Single UNHEALTHY route."""
    return _create_route_data(
        status=RouteStatus.UNHEALTHY,
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
    endpoint_id = uuid4()
    return [
        _create_route_data(
            endpoint_id=endpoint_id,
            status=RouteStatus.TERMINATING,
            session_id=SessionId(uuid4()),
        ),
        _create_route_data(
            endpoint_id=endpoint_id,
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
# Health Status Fixtures
# =============================================================================


@pytest.fixture
def health_status_healthy() -> MagicMock:
    """Healthy health status response."""
    status = MagicMock()
    status.get_status = MagicMock(return_value=HealthCheckStatus.HEALTHY)
    return status


@pytest.fixture
def health_status_unhealthy() -> MagicMock:
    """Unhealthy health status response."""
    status = MagicMock()
    status.get_status = MagicMock(return_value=HealthCheckStatus.UNHEALTHY)
    return status


@pytest.fixture
def health_status_stale() -> MagicMock:
    """Stale health status response."""
    status = MagicMock()
    status.get_status = MagicMock(return_value=HealthCheckStatus.STALE)
    return status


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
    config.cleanup_target_statuses = [RouteStatus.UNHEALTHY]
    return config


@pytest.fixture
def cleanup_config_unhealthy_and_degraded() -> MagicMock:
    """Cleanup config that targets UNHEALTHY and DEGRADED routes."""
    config = MagicMock()
    config.cleanup_target_statuses = [RouteStatus.UNHEALTHY, RouteStatus.DEGRADED]
    return config


# =============================================================================
# Health Check Config & Discovery Fixtures
# =============================================================================


@pytest.fixture
def health_check_ready_route() -> RouteData:
    """HEALTHY route created long ago (past initial_delay)."""
    return _create_route_data(
        status=RouteStatus.HEALTHY,
        session_id=SessionId(uuid4()),
        created_at=datetime.now(tzutc()) - timedelta(minutes=10),
    )


@pytest.fixture
def default_health_check_config() -> ModelHealthCheck:
    """Default health check configuration."""
    return ModelHealthCheck(
        path="/health",
        interval=10.0,
        max_retries=3,
        max_wait_time=15.0,
        expected_status_code=200,
        initial_delay=5.0,
    )


@pytest.fixture
def create_deployment_with_health_check() -> Callable[..., MagicMock]:
    """Factory fixture to create DeploymentInfo with health check config."""

    def _factory(
        endpoint_id: UUID,
        health_check_path: str = "/health",
    ) -> MagicMock:
        revision = MagicMock()
        revision.model_definition = MagicMock()
        revision.model_definition.health_check_config.return_value = ModelHealthCheck(
            path=health_check_path,
            interval=10.0,
            max_retries=3,
            max_wait_time=15.0,
            expected_status_code=200,
            initial_delay=5.0,
        )
        revision.execution.runtime_variant = "custom"

        dep = MagicMock()
        dep.id = endpoint_id
        dep.current_revision_id = uuid4()
        dep.resolve_revision_spec.return_value = revision
        return dep

    return _factory


@pytest.fixture
def create_discovery_info() -> Callable[..., RouteServiceDiscoveryInfo]:
    """Factory fixture to create RouteServiceDiscoveryInfo."""

    def _factory(
        route_id: UUID,
        endpoint_id: UUID,
        kernel_host: str = "10.0.0.1",
        kernel_port: int = 8080,
    ) -> RouteServiceDiscoveryInfo:
        return RouteServiceDiscoveryInfo(
            route_id=route_id,
            endpoint_id=endpoint_id,
            endpoint_name="test-endpoint",
            runtime_variant="custom",
            kernel_host=kernel_host,
            kernel_port=kernel_port,
            session_owner=uuid4(),
            project=uuid4(),
        )

    return _factory


@pytest.fixture
def create_health_status() -> Callable[..., HealthStatus]:
    """Factory fixture to create HealthStatus."""

    def _factory(
        readiness: HealthCheckStatus | None = None,
        last_readiness: int | None = None,
        consecutive_failures: int = 0,
        created_at: int = 0,
    ) -> HealthStatus:
        return HealthStatus(
            readiness=readiness,
            liveness=None,
            last_check=None,
            last_readiness=last_readiness,
            created_at=created_at,
            readiness_consecutive_failures=consecutive_failures,
        )

    return _factory
