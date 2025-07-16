from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection for Valkey stat client"""
    mock_redis_connection = MagicMock()
    # Set up the methods that will be called
    mock_redis_connection.get_user_time_binned_monthly_stats = AsyncMock(return_value={})
    mock_redis_connection.get_admin_time_binned_monthly_stats = AsyncMock(return_value={})
    # Add any other methods that might be called
    mock_redis_connection.connect = AsyncMock()
    mock_redis_connection.disconnect = AsyncMock()
    return mock_redis_connection


@pytest.fixture
def mock_storage_manager():
    """Mock storage session manager"""
    mock_storage_manager = MagicMock(spec=StorageSessionManager)
    return mock_storage_manager


@pytest.fixture
def mock_action_monitor():
    """Mock action monitor"""
    mock_action_monitor = MagicMock(spec=ActionMonitor)
    return mock_action_monitor


@pytest.fixture
def processors(
    database_fixture,
    database_engine,
    mock_storage_manager,
    mock_redis_connection,
    mock_action_monitor,
) -> UserProcessors:
    """Create UserProcessors instance with mocked dependencies"""
    agent_registry_mock = MagicMock()
    user_repository = UserRepository(db=database_engine)
    admin_user_repository = AdminUserRepository(db=database_engine)

    user_service = UserService(
        storage_manager=mock_storage_manager,
        valkey_stat_client=mock_redis_connection,
        agent_registry=agent_registry_mock,
        user_repository=user_repository,
        admin_user_repository=admin_user_repository,
    )

    return UserProcessors(
        user_service=user_service,
        action_monitors=[mock_action_monitor],
    )
