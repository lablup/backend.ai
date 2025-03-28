
from unittest.mock import MagicMock
import pytest

from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.users.service import UserService

@pytest.fixture
def mock_redis_connection():
    mock_redis_connection = MagicMock(spec=RedisConnectionInfo)
    return mock_redis_connection

@pytest.fixture
def mock_storage_manager():
    mock_storage_manager = MagicMock(spec=StorageSessionManager)
    return mock_storage_manager


@pytest.fixture
def processors(database_engine, mock_storage_manager, mock_redis_connection) -> UserProcessors:
    user_service = UserService(
        db=database_engine,
        storage_manager=mock_storage_manager,
        redis_stat=mock_redis_connection
    )
    return UserProcessors(user_service=user_service)

