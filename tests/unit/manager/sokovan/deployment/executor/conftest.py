"""Fixtures for DeploymentExecutor tests."""

from __future__ import annotations

from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentState,
    ModelRevisionData,
    ReplicaData,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory

# =============================================================================
# Mock Dependencies
# =============================================================================


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    """Mock DeploymentRepository."""
    repo = AsyncMock()
    repo.fetch_scaling_group_proxy_targets = AsyncMock(return_value={})
    repo.fetch_active_routes_by_endpoint_ids = AsyncMock(return_value={})
    repo.update_endpoint_url = AsyncMock(return_value=None)
    repo.update_desired_replicas_bulk = AsyncMock(return_value=None)
    repo.mark_terminating_route_status_bulk = AsyncMock(return_value=None)
    repo.scale_routes = AsyncMock(return_value=None)
    repo.fetch_auto_scaling_rules_by_endpoint_ids = AsyncMock(return_value={})
    repo.fetch_metrics_for_autoscaling = AsyncMock(return_value=MagicMock())
    repo.calculate_desired_replicas_for_deployment = AsyncMock(return_value=None)
    mock_revision_spec = MagicMock()
    mock_revision_spec.execution.runtime_variant = RuntimeVariant("custom")
    repo.get_revision_spec_from_endpoint = AsyncMock(return_value=mock_revision_spec)
    return repo


@pytest.fixture
def mock_scheduling_controller() -> AsyncMock:
    """Mock SchedulingController."""
    return AsyncMock()


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    return MagicMock()


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
    return AsyncMock()


@pytest.fixture
def mock_prometheus_client() -> AsyncMock:
    """Mock PrometheusClient for Prometheus-based auto-scaling."""
    return AsyncMock()


@pytest.fixture
def mock_preset_repo() -> AsyncMock:
    """Mock PrometheusQueryPresetRepository for Prometheus-based auto-scaling."""
    return AsyncMock()


@pytest.fixture
def deployment_executor(
    mock_deployment_repo: AsyncMock,
    mock_scheduling_controller: AsyncMock,
    mock_config_provider: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_stat: AsyncMock,
    mock_prometheus_client: AsyncMock,
    mock_preset_repo: AsyncMock,
) -> DeploymentExecutor:
    """Create DeploymentExecutor with mocked dependencies."""
    return DeploymentExecutor(
        deployment_repo=mock_deployment_repo,
        runtime_variant_repo=AsyncMock(),
        scheduling_controller=mock_scheduling_controller,
        config_provider=mock_config_provider,
        client_pool=mock_client_pool,
        valkey_stat=mock_valkey_stat,
        prometheus_client=mock_prometheus_client,
        preset_repo=mock_preset_repo,
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
    rev_id = uuid4()
    revision = MagicMock() if has_revision else None
    if revision is not None:
        revision.id = rev_id

    return DeploymentInfo(
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
            replica_count=replica_count,
            desired_replica_count=desired_replica_count,
        ),
        network=DeploymentNetworkData(
            open_to_public=False,
            access_token_ids=None,
            url=None,
            preferred_domain_name=None,
        ),
        options=DeploymentOptions(),
        current_revision=cast(ModelRevisionData, revision) if has_revision else None,
    )


def _create_route_data(
    route_id: UUID | None = None,
    endpoint_id: UUID | None = None,
    status: RouteStatus = RouteStatus.RUNNING,
    health_status: RouteHealthStatus = RouteHealthStatus.HEALTHY,
) -> RouteData:
    """Create RouteData for tests."""
    return RouteData(
        route_id=ReplicaID(route_id) if route_id is not None else ReplicaID(uuid4()),
        deployment_id=DeploymentID(endpoint_id or uuid4()),
        session_id=None,
        status=status,
        health_status=health_status,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
    )


@pytest.fixture
def pending_deployment() -> DeploymentWithHistory:
    """Single PENDING deployment for check_pending tests."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(lifecycle=EndpointLifecycle.PENDING),
        last_history=None,
    )


@pytest.fixture
def pending_deployments_multiple() -> list[DeploymentWithHistory]:
    """Multiple PENDING deployments."""
    return [
        DeploymentWithHistory(
            deployment_info=_create_deployment_info(
                lifecycle=EndpointLifecycle.PENDING, resource_group="sg-1"
            ),
            last_history=None,
        ),
        DeploymentWithHistory(
            deployment_info=_create_deployment_info(
                lifecycle=EndpointLifecycle.PENDING, resource_group="sg-2"
            ),
            last_history=None,
        ),
    ]


@pytest.fixture
def pending_deployment_no_revision() -> DeploymentWithHistory:
    """PENDING deployment without target revision."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(
            lifecycle=EndpointLifecycle.PENDING, has_revision=False
        ),
        last_history=None,
    )


@pytest.fixture
def ready_deployment() -> DeploymentWithHistory:
    """READY deployment for scaling tests."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(
            lifecycle=EndpointLifecycle.READY,
            desired_replica_count=2,
            replica_count=2,
        ),
        last_history=None,
    )


@pytest.fixture
def ready_deployment_needs_scale_up() -> DeploymentWithHistory:
    """READY deployment that needs scale up."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(
            lifecycle=EndpointLifecycle.READY,
            desired_replica_count=3,
            replica_count=2,
        ),
        last_history=None,
    )


@pytest.fixture
def ready_deployment_needs_scale_down() -> DeploymentWithHistory:
    """READY deployment that needs scale down."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(
            lifecycle=EndpointLifecycle.READY,
            desired_replica_count=1,
            replica_count=2,
        ),
        last_history=None,
    )


@pytest.fixture
def destroying_deployment() -> DeploymentWithHistory:
    """DESTROYING deployment for termination tests."""
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(lifecycle=EndpointLifecycle.DESTROYING),
        last_history=None,
    )


@pytest.fixture
def ready_deployment_no_current_revision() -> DeploymentWithHistory:
    """READY deployment whose current_revision was never set / was cleared.

    Exercises the guard that keeps check_ready / calculate_desired_replicas
    from transitioning a revisionless deployment into SCALING (where it
    would then get wedged because scale_deployment() also skips it).
    """
    return DeploymentWithHistory(
        deployment_info=_create_deployment_info(
            lifecycle=EndpointLifecycle.READY,
            desired_replica_count=2,
            replica_count=2,
            has_revision=False,
        ),
        last_history=None,
    )


@pytest.fixture
def destroying_deployments_multiple() -> list[DeploymentWithHistory]:
    """Multiple DESTROYING deployments."""
    return [
        DeploymentWithHistory(
            deployment_info=_create_deployment_info(
                lifecycle=EndpointLifecycle.DESTROYING, resource_group="sg-1"
            ),
            last_history=None,
        ),
        DeploymentWithHistory(
            deployment_info=_create_deployment_info(
                lifecycle=EndpointLifecycle.DESTROYING, resource_group="sg-2"
            ),
            last_history=None,
        ),
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
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
    ]


@pytest.fixture
def routes_fewer_than_replicas() -> list[RouteData]:
    """Routes fewer than target replica count."""
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
    ]


@pytest.fixture
def routes_more_than_replicas() -> list[RouteData]:
    """Routes more than target replica count."""
    endpoint_id = uuid4()
    return [
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
        _create_route_data(endpoint_id=endpoint_id, status=RouteStatus.RUNNING),
    ]
