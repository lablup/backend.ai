"""
Mock-based fixtures for ModelServingService and AutoScalingService unit tests.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


@pytest.fixture
def mock_redis_connection() -> MagicMock:
    """Mock ValkeyStatClient for testing."""
    return MagicMock(spec=ValkeyStatClient)


@pytest.fixture
def mock_storage_manager() -> MagicMock:
    """Mock StorageSessionManager for testing."""
    return MagicMock(spec=StorageSessionManager)


@pytest.fixture
def mock_action_monitor() -> MagicMock:
    """Mock ActionMonitor for testing."""
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def mock_event_dispatcher() -> MagicMock:
    """Mock EventDispatcher for testing."""
    mock = MagicMock(spec=EventDispatcher)
    mock.dispatch = AsyncMock()
    return mock


@pytest.fixture
def mock_agent_registry() -> MagicMock:
    """Mock AgentRegistry for testing."""
    return MagicMock(spec=AgentRegistry)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Mock ManagerConfigProvider for testing."""
    return MagicMock(spec=ManagerConfigProvider)


@pytest.fixture
def mock_repositories() -> MagicMock:
    """Mock ModelServingRepositories for testing."""
    mock = MagicMock(spec=ModelServingRepositories)
    mock.repository = MagicMock(spec=ModelServingRepository)
    mock.admin_repository = MagicMock(spec=AdminModelServingRepository)
    return mock


@pytest.fixture
def mock_background_task_manager() -> MagicMock:
    """Mock BackgroundTaskManager for testing."""
    return MagicMock(spec=BackgroundTaskManager)


@pytest.fixture
def mock_valkey_live() -> MagicMock:
    """Mock valkey live client for testing."""
    mock = MagicMock()
    mock.store_live_data = AsyncMock()
    mock.get_live_data = AsyncMock()
    mock.delete_live_data = AsyncMock()
    return mock


@pytest.fixture
def mock_deployment_controller() -> MagicMock:
    """Mock DeploymentController for testing."""
    mock = MagicMock(spec=DeploymentController)
    mock.mark_lifecycle_needed = AsyncMock()
    return mock


@pytest.fixture
def mock_event_hub() -> MagicMock:
    """Mock EventHub for testing."""
    mock = MagicMock(spec=EventHub)
    mock.register_event_propagator = MagicMock()
    mock.unregister_event_propagator = MagicMock()
    return mock


@pytest.fixture
def mock_scheduling_controller() -> MagicMock:
    """Mock SchedulingController for testing."""
    mock = MagicMock(spec=SchedulingController)
    mock.enqueue_session = AsyncMock()
    mock.mark_sessions_for_termination = AsyncMock()
    return mock


@pytest.fixture
def model_serving_service(
    mock_storage_manager: MagicMock,
    mock_event_dispatcher: MagicMock,
    mock_event_hub: MagicMock,
    mock_agent_registry: MagicMock,
    mock_background_task_manager: MagicMock,
    mock_config_provider: MagicMock,
    mock_valkey_live: MagicMock,
    mock_repositories: MagicMock,
    mock_deployment_controller: MagicMock,
    mock_scheduling_controller: MagicMock,
) -> ModelServingService:
    """Create ModelServingService with mock dependencies."""
    return ModelServingService(
        agent_registry=mock_agent_registry,
        background_task_manager=mock_background_task_manager,
        event_dispatcher=mock_event_dispatcher,
        event_hub=mock_event_hub,
        storage_manager=mock_storage_manager,
        config_provider=mock_config_provider,
        valkey_live=mock_valkey_live,
        repository=mock_repositories.repository,
        admin_repository=mock_repositories.admin_repository,
        deployment_controller=mock_deployment_controller,
        scheduling_controller=mock_scheduling_controller,
    )


@pytest.fixture
def model_serving_processors(
    mock_action_monitor: MagicMock,
    model_serving_service: ModelServingService,
) -> ModelServingProcessors:
    """Create ModelServingProcessors with mock dependencies."""
    return ModelServingProcessors(
        service=model_serving_service,
        action_monitors=[mock_action_monitor],
    )


@pytest.fixture
def auto_scaling_service(
    mock_repositories: MagicMock,
) -> AutoScalingService:
    """Create AutoScalingService with mock dependencies."""
    return AutoScalingService(
        repository=mock_repositories.repository,
        admin_repository=mock_repositories.admin_repository,
    )


@pytest.fixture
def auto_scaling_processors(
    mock_action_monitor: MagicMock,
    auto_scaling_service: AutoScalingService,
) -> ModelServingAutoScalingProcessors:
    """Create ModelServingAutoScalingProcessors with mock dependencies."""
    return ModelServingAutoScalingProcessors(
        service=auto_scaling_service,
        action_monitors=[mock_action_monitor],
    )
