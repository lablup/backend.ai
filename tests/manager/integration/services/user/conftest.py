from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


@pytest.fixture
def processors(
    database_fixture,
    database_engine,
    registry_ctx,
) -> UserProcessors:
    """Create UserProcessors instance with real dependencies for integration testing"""
    agent_registry, _, _, _, _, _, _ = registry_ctx
    user_repository = UserRepository(db=database_engine)
    admin_user_repository = AdminUserRepository(db=database_engine)

    # Use minimal mocks only for dependencies that are not core to user operations
    storage_manager_mock = MagicMock(spec=StorageSessionManager)
    valkey_stat_client_mock = MagicMock(spec=ValkeyStatClient)
    # Mock the async methods that are called in stats operations
    valkey_stat_client_mock.get_user_time_binned_monthly_stats = AsyncMock(return_value=[])
    valkey_stat_client_mock.get_admin_time_binned_monthly_stats = AsyncMock(return_value=[])

    user_service = UserService(
        storage_manager=storage_manager_mock,
        valkey_stat_client=valkey_stat_client_mock,
        agent_registry=agent_registry,
        user_repository=user_repository,
        admin_user_repository=admin_user_repository,
    )

    return UserProcessors(
        user_service=user_service,
        action_monitors=[],
    )
