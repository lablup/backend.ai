"""Tests for RouteCoordinator history recording integration."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.deployment.route.handlers.base import RouteHandler
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionError,
    RouteExecutionResult,
    RouteLifecycleType,
)

if TYPE_CHECKING:
    from collections.abc import Generator


# ============================================================
# Fixtures for sample data
# ============================================================


@pytest.fixture
def sample_route_data() -> RouteData:
    """Sample RouteData for testing."""
    return RouteData(
        route_id=uuid4(),
        endpoint_id=uuid4(),
        session_id=None,
        status=RouteStatus.PROVISIONING,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
    )


@pytest.fixture
def sample_route_execution_error(
    sample_route_data: RouteData,
) -> RouteExecutionError:
    """Sample RouteExecutionError for testing."""
    return RouteExecutionError(
        route_info=sample_route_data,
        reason="Test failure",
        error_detail="Detailed error message",
    )


# ============================================================
# Fixtures for mock dependencies
# ============================================================


@pytest.fixture
def mock_deployment_repository() -> AsyncMock:
    """Mock DeploymentRepository with minimal implementation."""
    mock = AsyncMock(spec=DeploymentRepository)
    mock.get_routes_by_statuses = AsyncMock(return_value=[])
    mock.update_route_status_bulk_with_history = AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    return AsyncMock()


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    """Mock EventProducer."""
    return AsyncMock()


@pytest.fixture
def mock_lock_factory() -> MagicMock:
    """Mock DistributedLockFactory that returns async context manager."""
    mock = MagicMock()
    mock.return_value.__aenter__ = AsyncMock()
    mock.return_value.__aexit__ = AsyncMock()
    return mock


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider."""
    mock = MagicMock()
    mock.config.manager.session_schedule_lock_lifetime = 30.0
    return mock


@pytest.fixture
def mock_scheduling_controller() -> MagicMock:
    """Mock SchedulingController."""
    return MagicMock()


@pytest.fixture
def mock_client_pool() -> MagicMock:
    """Mock ClientPool."""
    return MagicMock()


@pytest.fixture
def mock_service_discovery() -> MagicMock:
    """Mock ServiceDiscovery."""
    return MagicMock()


# ============================================================
# Fixtures for mock handlers with different scenarios
# ============================================================


@pytest.fixture
def mock_handler_with_success(
    sample_route_data: RouteData,
) -> MagicMock:
    """Handler that returns success result."""
    mock = MagicMock(spec=RouteHandler)
    mock.name = MagicMock(return_value="provisioning")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[RouteStatus.PROVISIONING])
    mock.next_status = MagicMock(return_value=RouteStatus.HEALTHY)
    mock.failure_status = MagicMock(return_value=None)
    mock.stale_status = MagicMock(return_value=None)
    mock.execute = AsyncMock(
        return_value=RouteExecutionResult(
            successes=[sample_route_data],
            errors=[],
            stale=[],
        )
    )
    mock.post_process = AsyncMock()
    return mock


@pytest.fixture
def mock_handler_with_failure(
    sample_route_execution_error: RouteExecutionError,
) -> MagicMock:
    """Handler that returns failure result."""
    mock = MagicMock(spec=RouteHandler)
    mock.name = MagicMock(return_value="provisioning")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[RouteStatus.PROVISIONING])
    mock.next_status = MagicMock(return_value=RouteStatus.HEALTHY)
    mock.failure_status = MagicMock(return_value=RouteStatus.FAILED_TO_START)
    mock.stale_status = MagicMock(return_value=None)
    mock.execute = AsyncMock(
        return_value=RouteExecutionResult(
            successes=[],
            errors=[sample_route_execution_error],
            stale=[],
        )
    )
    mock.post_process = AsyncMock()
    return mock


@pytest.fixture
def mock_handler_with_stale(
    sample_route_data: RouteData,
) -> MagicMock:
    """Handler that returns stale result."""
    mock = MagicMock(spec=RouteHandler)
    mock.name = MagicMock(return_value="health_check")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[RouteStatus.HEALTHY])
    mock.next_status = MagicMock(return_value=None)
    mock.failure_status = MagicMock(return_value=None)
    mock.stale_status = MagicMock(return_value=RouteStatus.UNHEALTHY)
    mock.execute = AsyncMock(
        return_value=RouteExecutionResult(
            successes=[],
            errors=[],
            stale=[sample_route_data],
        )
    )
    mock.post_process = AsyncMock()
    return mock


@pytest.fixture
def mock_handler_with_empty_result() -> MagicMock:
    """Handler that returns empty result."""
    mock = MagicMock(spec=RouteHandler)
    mock.name = MagicMock(return_value="provisioning")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[RouteStatus.PROVISIONING])
    mock.next_status = MagicMock(return_value=RouteStatus.HEALTHY)
    mock.failure_status = MagicMock(return_value=None)
    mock.stale_status = MagicMock(return_value=None)
    mock.execute = AsyncMock(return_value=RouteExecutionResult())
    mock.post_process = AsyncMock()
    return mock


# ============================================================
# Fixtures for coordinator scenarios
# ============================================================


@pytest.fixture
def coordinator_with_provisioning_routes(
    mock_valkey_schedule: AsyncMock,
    mock_deployment_repository: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_lock_factory: MagicMock,
    mock_config_provider: MagicMock,
    mock_scheduling_controller: MagicMock,
    mock_client_pool: MagicMock,
    mock_service_discovery: MagicMock,
    sample_route_data: RouteData,
) -> Generator[RouteCoordinator, None, None]:
    """Coordinator with PROVISIONING routes available."""
    mock_deployment_repository.get_routes_by_statuses = AsyncMock(return_value=[sample_route_data])

    coordinator = RouteCoordinator(
        valkey_schedule=mock_valkey_schedule,
        deployment_repository=mock_deployment_repository,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
        config_provider=mock_config_provider,
        scheduling_controller=mock_scheduling_controller,
        client_pool=mock_client_pool,
        service_discovery=mock_service_discovery,
    )
    yield coordinator


@pytest.fixture
def coordinator_without_routes(
    mock_valkey_schedule: AsyncMock,
    mock_deployment_repository: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_lock_factory: MagicMock,
    mock_config_provider: MagicMock,
    mock_scheduling_controller: MagicMock,
    mock_client_pool: MagicMock,
    mock_service_discovery: MagicMock,
) -> Generator[RouteCoordinator, None, None]:
    """Coordinator with no routes available."""
    mock_deployment_repository.get_routes_by_statuses = AsyncMock(return_value=[])

    coordinator = RouteCoordinator(
        valkey_schedule=mock_valkey_schedule,
        deployment_repository=mock_deployment_repository,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
        config_provider=mock_config_provider,
        scheduling_controller=mock_scheduling_controller,
        client_pool=mock_client_pool,
        service_discovery=mock_service_discovery,
    )
    yield coordinator


# ============================================================
# Test cases for process_route_lifecycle
# ============================================================


class TestProcessRouteLifecycle:
    """Tests for process_route_lifecycle public method."""

    @pytest.mark.asyncio
    async def test_records_history_on_success(
        self,
        coordinator_with_provisioning_routes: RouteCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_success: MagicMock,
    ) -> None:
        """History is recorded when handler returns success."""
        coordinator_with_provisioning_routes._route_handlers = {
            RouteLifecycleType.PROVISIONING: mock_handler_with_success
        }

        await coordinator_with_provisioning_routes.process_route_lifecycle(
            RouteLifecycleType.PROVISIONING
        )

        mock_deployment_repository.update_route_status_bulk_with_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_history_on_failure(
        self,
        coordinator_with_provisioning_routes: RouteCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_failure: MagicMock,
    ) -> None:
        """History is recorded when handler returns failure."""
        coordinator_with_provisioning_routes._route_handlers = {
            RouteLifecycleType.PROVISIONING: mock_handler_with_failure
        }

        await coordinator_with_provisioning_routes.process_route_lifecycle(
            RouteLifecycleType.PROVISIONING
        )

        mock_deployment_repository.update_route_status_bulk_with_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_history_on_stale(
        self,
        coordinator_with_provisioning_routes: RouteCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_stale: MagicMock,
    ) -> None:
        """History is recorded when handler returns stale routes."""
        coordinator_with_provisioning_routes._route_handlers = {
            RouteLifecycleType.HEALTH_CHECK: mock_handler_with_stale
        }
        # Update repository mock to return routes for HEALTHY status
        mock_deployment_repository.get_routes_by_statuses = AsyncMock(
            return_value=[
                RouteData(
                    route_id=uuid4(),
                    endpoint_id=uuid4(),
                    session_id=None,
                    status=RouteStatus.HEALTHY,
                    traffic_ratio=1.0,
                    created_at=datetime.now(tzutc()),
                )
            ]
        )

        await coordinator_with_provisioning_routes.process_route_lifecycle(
            RouteLifecycleType.HEALTH_CHECK
        )

        mock_deployment_repository.update_route_status_bulk_with_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_history_when_no_routes(
        self,
        coordinator_without_routes: RouteCoordinator,
        mock_deployment_repository: AsyncMock,
    ) -> None:
        """History is not recorded when no routes to process."""
        await coordinator_without_routes.process_route_lifecycle(RouteLifecycleType.PROVISIONING)

        mock_deployment_repository.update_route_status_bulk_with_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_history_when_handler_returns_empty(
        self,
        coordinator_with_provisioning_routes: RouteCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_empty_result: MagicMock,
    ) -> None:
        """History is not recorded when handler returns empty result."""
        coordinator_with_provisioning_routes._route_handlers = {
            RouteLifecycleType.PROVISIONING: mock_handler_with_empty_result
        }

        await coordinator_with_provisioning_routes.process_route_lifecycle(
            RouteLifecycleType.PROVISIONING
        )

        mock_deployment_repository.update_route_status_bulk_with_history.assert_not_called()
