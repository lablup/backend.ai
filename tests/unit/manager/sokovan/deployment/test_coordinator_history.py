"""Tests for DeploymentCoordinator history recording integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.handlers.base import DeploymentHandler
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)

if TYPE_CHECKING:
    from collections.abc import Generator


# ============================================================
# Fixtures for sample data
# ============================================================


@pytest.fixture
def sample_deployment_info() -> DeploymentInfo:
    """Sample DeploymentInfo for testing."""
    return DeploymentInfo(
        id=uuid4(),
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group="default",
            created_user=uuid4(),
            session_owner=uuid4(),
            created_at=None,
            revision_history_limit=5,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.PENDING,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=1,
            desired_replica_count=None,
        ),
        network=DeploymentNetworkSpec(
            open_to_public=False,
        ),
        model_revisions=[],
    )


@pytest.fixture
def sample_deployment_execution_error(
    sample_deployment_info: DeploymentInfo,
) -> DeploymentExecutionError:
    """Sample DeploymentExecutionError for testing."""
    return DeploymentExecutionError(
        deployment_info=sample_deployment_info,
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
    mock.get_endpoints_by_statuses = AsyncMock(return_value=[])
    mock.update_endpoint_lifecycle_bulk_with_history = AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_valkey_schedule() -> AsyncMock:
    """Mock ValkeyScheduleClient."""
    return AsyncMock()


@pytest.fixture
def mock_deployment_controller() -> MagicMock:
    """Mock DeploymentController."""
    return MagicMock()


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
def mock_valkey_stat() -> AsyncMock:
    """Mock ValkeyStatClient."""
    return AsyncMock()


@pytest.fixture
def mock_route_controller() -> MagicMock:
    """Mock RouteController."""
    return MagicMock()


# ============================================================
# Fixtures for mock handlers with different scenarios
# ============================================================


@pytest.fixture
def mock_handler_with_success(
    sample_deployment_info: DeploymentInfo,
) -> MagicMock:
    """Handler that returns success result."""
    mock = MagicMock(spec=DeploymentHandler)
    mock.name = MagicMock(return_value="check_pending")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[EndpointLifecycle.PENDING])
    mock.next_status = MagicMock(return_value=EndpointLifecycle.CREATED)
    mock.failure_status = MagicMock(return_value=None)
    mock.execute = AsyncMock(
        return_value=DeploymentExecutionResult(
            successes=[sample_deployment_info],
            errors=[],
        )
    )
    mock.post_process = AsyncMock()
    return mock


@pytest.fixture
def mock_handler_with_failure(
    sample_deployment_execution_error: DeploymentExecutionError,
) -> MagicMock:
    """Handler that returns failure result."""
    mock = MagicMock(spec=DeploymentHandler)
    mock.name = MagicMock(return_value="check_pending")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[EndpointLifecycle.PENDING])
    mock.next_status = MagicMock(return_value=EndpointLifecycle.CREATED)
    mock.failure_status = MagicMock(return_value=EndpointLifecycle.DESTROYED)
    mock.execute = AsyncMock(
        return_value=DeploymentExecutionResult(
            successes=[],
            errors=[sample_deployment_execution_error],
        )
    )
    mock.post_process = AsyncMock()
    return mock


@pytest.fixture
def mock_handler_with_empty_result() -> MagicMock:
    """Handler that returns empty result."""
    mock = MagicMock(spec=DeploymentHandler)
    mock.name = MagicMock(return_value="check_pending")
    mock.lock_id = None
    mock.target_statuses = MagicMock(return_value=[EndpointLifecycle.PENDING])
    mock.next_status = MagicMock(return_value=EndpointLifecycle.CREATED)
    mock.failure_status = MagicMock(return_value=None)
    mock.execute = AsyncMock(return_value=DeploymentExecutionResult())
    mock.post_process = AsyncMock()
    return mock


# ============================================================
# Fixtures for coordinator scenarios
# ============================================================


@pytest.fixture
def coordinator_with_pending_deployments(
    mock_valkey_schedule: AsyncMock,
    mock_deployment_controller: MagicMock,
    mock_deployment_repository: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_lock_factory: MagicMock,
    mock_config_provider: MagicMock,
    mock_scheduling_controller: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_stat: AsyncMock,
    mock_route_controller: MagicMock,
    sample_deployment_info: DeploymentInfo,
) -> Generator[DeploymentCoordinator, None, None]:
    """Coordinator with PENDING deployments available."""
    mock_deployment_repository.get_endpoints_by_statuses = AsyncMock(
        return_value=[sample_deployment_info]
    )

    coordinator = DeploymentCoordinator(
        valkey_schedule=mock_valkey_schedule,
        deployment_controller=mock_deployment_controller,
        deployment_repository=mock_deployment_repository,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
        config_provider=mock_config_provider,
        scheduling_controller=mock_scheduling_controller,
        client_pool=mock_client_pool,
        valkey_stat=mock_valkey_stat,
        route_controller=mock_route_controller,
    )
    yield coordinator


@pytest.fixture
def coordinator_without_deployments(
    mock_valkey_schedule: AsyncMock,
    mock_deployment_controller: MagicMock,
    mock_deployment_repository: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_lock_factory: MagicMock,
    mock_config_provider: MagicMock,
    mock_scheduling_controller: MagicMock,
    mock_client_pool: MagicMock,
    mock_valkey_stat: AsyncMock,
    mock_route_controller: MagicMock,
) -> Generator[DeploymentCoordinator, None, None]:
    """Coordinator with no deployments available."""
    mock_deployment_repository.get_endpoints_by_statuses = AsyncMock(return_value=[])

    coordinator = DeploymentCoordinator(
        valkey_schedule=mock_valkey_schedule,
        deployment_controller=mock_deployment_controller,
        deployment_repository=mock_deployment_repository,
        event_producer=mock_event_producer,
        lock_factory=mock_lock_factory,
        config_provider=mock_config_provider,
        scheduling_controller=mock_scheduling_controller,
        client_pool=mock_client_pool,
        valkey_stat=mock_valkey_stat,
        route_controller=mock_route_controller,
    )
    yield coordinator


# ============================================================
# Test cases for process_deployment_lifecycle
# ============================================================


class TestProcessDeploymentLifecycle:
    """Tests for process_deployment_lifecycle public method."""

    @pytest.mark.asyncio
    async def test_records_history_on_success(
        self,
        coordinator_with_pending_deployments: DeploymentCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_success: MagicMock,
    ) -> None:
        """History is recorded when handler returns success."""
        coordinator_with_pending_deployments._deployment_handlers = {
            DeploymentLifecycleType.CHECK_PENDING: mock_handler_with_success
        }

        await coordinator_with_pending_deployments.process_deployment_lifecycle(
            DeploymentLifecycleType.CHECK_PENDING
        )

        mock_deployment_repository.update_endpoint_lifecycle_bulk_with_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_history_on_failure(
        self,
        coordinator_with_pending_deployments: DeploymentCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_failure: MagicMock,
    ) -> None:
        """History is recorded when handler returns failure."""
        coordinator_with_pending_deployments._deployment_handlers = {
            DeploymentLifecycleType.CHECK_PENDING: mock_handler_with_failure
        }

        await coordinator_with_pending_deployments.process_deployment_lifecycle(
            DeploymentLifecycleType.CHECK_PENDING
        )

        mock_deployment_repository.update_endpoint_lifecycle_bulk_with_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_history_when_no_deployments(
        self,
        coordinator_without_deployments: DeploymentCoordinator,
        mock_deployment_repository: AsyncMock,
    ) -> None:
        """History is not recorded when no deployments to process."""
        await coordinator_without_deployments.process_deployment_lifecycle(
            DeploymentLifecycleType.CHECK_PENDING
        )

        mock_deployment_repository.update_endpoint_lifecycle_bulk_with_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_history_when_handler_returns_empty(
        self,
        coordinator_with_pending_deployments: DeploymentCoordinator,
        mock_deployment_repository: AsyncMock,
        mock_handler_with_empty_result: MagicMock,
    ) -> None:
        """History is not recorded when handler returns empty result."""
        coordinator_with_pending_deployments._deployment_handlers = {
            DeploymentLifecycleType.CHECK_PENDING: mock_handler_with_empty_result
        }

        await coordinator_with_pending_deployments.process_deployment_lifecycle(
            DeploymentLifecycleType.CHECK_PENDING
        )

        mock_deployment_repository.update_endpoint_lifecycle_bulk_with_history.assert_not_called()
