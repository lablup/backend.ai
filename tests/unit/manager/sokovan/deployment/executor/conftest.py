"""Fixtures for DeploymentExecutor tests."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
    RouteStatus,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    """Mock DeploymentRepository."""
    repo = AsyncMock()
    repo.fetch_scaling_group_proxy_targets = AsyncMock(return_value={})
    repo.fetch_active_routes_by_endpoint_ids = AsyncMock(return_value={})
    repo.update_endpoint_urls_bulk = AsyncMock(return_value=None)
    repo.update_desired_replicas_bulk = AsyncMock(return_value=None)
    repo.mark_terminating_route_status_bulk = AsyncMock(return_value=None)
    repo.scale_routes = AsyncMock(return_value=None)
    repo.fetch_auto_scaling_rules_by_endpoint_ids = AsyncMock(return_value={})
    repo.fetch_metrics_for_autoscaling = AsyncMock(return_value=MagicMock())
    repo.calculate_desired_replicas_for_deployment = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_scheduling_controller() -> AsyncMock:
    """Mock SchedulingController."""
    controller = AsyncMock()
    return controller


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    provider = MagicMock()
    provider.config.deployment.enable_model_definition_override = False
    return provider


@pytest.fixture
def mock_client_pool() -> MagicMock:
    """Mock ClientPool."""
    pool = MagicMock()
    mock_session = MagicMock()
    pool.load_client_session = MagicMock(return_value=mock_session)
    return pool


@pytest.fixture
def mock_valkey_stat() -> AsyncMock:
    """Mock ValkeyStatClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def deployment_executor(
    mock_deployment_repo: AsyncMock,
    mock_scheduling_controller: AsyncMock,
    mock_config_provider: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_stat: AsyncMock,
) -> DeploymentExecutor:
    """Create DeploymentExecutor with mocked dependencies."""
    return DeploymentExecutor(
        deployment_repo=mock_deployment_repo,
        scheduling_controller=mock_scheduling_controller,
        config_provider=mock_config_provider,
        client_pool=mock_client_pool,
        valkey_stat=mock_valkey_stat,
    )


# =============================================================================
# DeploymentInfo Fixtures
# =============================================================================


def _create_deployment_info(
    deployment_id: UUID | None = None,
    lifecycle: EndpointLifecycle = EndpointLifecycle.PENDING,
    desired_replica_count: int | None = None,
    replica_count: int = 1,
    resource_group: str = "default",
    has_revision: bool = True,
) -> DeploymentInfo:
    """Create DeploymentInfo for tests."""
    dep_id = deployment_id or uuid4()
    revision = MagicMock() if has_revision else None

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
            replica_count=replica_count,
            desired_replica_count=desired_replica_count,
        ),
        network=DeploymentNetworkSpec(
            open_to_public=False,
            url=None,
        ),
        model_revisions=[revision] if has_revision else [],  # type: ignore[list-item]
        current_revision_id=uuid4() if has_revision else None,
    )


def _create_route_data(
    route_id: UUID | None = None,
    endpoint_id: UUID | None = None,
    status: RouteStatus = RouteStatus.HEALTHY,
) -> RouteData:
    """Create RouteData for tests."""
    return RouteData(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id or uuid4(),
        session_id=None,
        status=status,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
    )


@pytest.fixture
def pending_deployment() -> DeploymentInfo:
    """Single PENDING deployment for check_pending tests."""
    return _create_deployment_info(lifecycle=EndpointLifecycle.PENDING)


@pytest.fixture
def pending_deployments_multiple() -> list[DeploymentInfo]:
    """Multiple PENDING deployments."""
    return [
        _create_deployment_info(lifecycle=EndpointLifecycle.PENDING, resource_group="sg-1"),
        _create_deployment_info(lifecycle=EndpointLifecycle.PENDING, resource_group="sg-2"),
    ]


@pytest.fixture
def pending_deployment_no_revision() -> DeploymentInfo:
    """PENDING deployment without target revision."""
    return _create_deployment_info(lifecycle=EndpointLifecycle.PENDING, has_revision=False)


@pytest.fixture
def ready_deployment() -> DeploymentInfo:
    """READY deployment for scaling tests."""
    return _create_deployment_info(
        lifecycle=EndpointLifecycle.READY,
        desired_replica_count=2,
        replica_count=2,
    )


@pytest.fixture
def ready_deployment_needs_scale_up() -> DeploymentInfo:
    """READY deployment that needs scale up."""
    return _create_deployment_info(
        lifecycle=EndpointLifecycle.READY,
        desired_replica_count=3,
        replica_count=2,
    )


@pytest.fixture
def ready_deployment_needs_scale_down() -> DeploymentInfo:
    """READY deployment that needs scale down."""
    return _create_deployment_info(
        lifecycle=EndpointLifecycle.READY,
        desired_replica_count=1,
        replica_count=2,
    )


@pytest.fixture
def destroying_deployment() -> DeploymentInfo:
    """DESTROYING deployment for termination tests."""
    return _create_deployment_info(lifecycle=EndpointLifecycle.DESTROYING)


@pytest.fixture
def destroying_deployments_multiple() -> list[DeploymentInfo]:
    """Multiple DESTROYING deployments."""
    return [
        _create_deployment_info(lifecycle=EndpointLifecycle.DESTROYING, resource_group="sg-1"),
        _create_deployment_info(lifecycle=EndpointLifecycle.DESTROYING, resource_group="sg-2"),
    ]


# =============================================================================
# Proxy Target Fixtures
# =============================================================================


@pytest.fixture
def proxy_target_default() -> ScalingGroupProxyTarget:
    """Default proxy target for tests."""
    return ScalingGroupProxyTarget(
        addr="http://proxy:8080",
        api_token="test-token",
    )


@pytest.fixture
def proxy_targets_by_scaling_group(
    proxy_target_default: ScalingGroupProxyTarget,
) -> dict[str, ScalingGroupProxyTarget]:
    """Proxy targets mapped by scaling group."""
    return {
        "default": proxy_target_default,
        "sg-1": proxy_target_default,
        "sg-2": proxy_target_default,
    }


# =============================================================================
# Route Fixtures
# =============================================================================


@pytest.fixture
def routes_matching_replicas() -> list[RouteData]:
    """Routes matching target replica count."""
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
    ]


@pytest.fixture
def routes_fewer_than_replicas() -> list[RouteData]:
    """Routes fewer than target replica count."""
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
    ]


@pytest.fixture
def routes_more_than_replicas() -> list[RouteData]:
    """Routes more than target replica count."""
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.HEALTHY),
    ]
