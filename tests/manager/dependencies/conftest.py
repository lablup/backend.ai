from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@pytest.fixture
def mock_etcd() -> AsyncEtcd:
    """

    Fixture providing a mock AsyncEtcd instance.
    """
    mock = MagicMock(spec=AsyncEtcd)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_db_engine() -> ExtendedAsyncSAEngine:
    """

    Fixture providing a mock database engine.
    """
    mock = MagicMock(spec=ExtendedAsyncSAEngine)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_config() -> ManagerUnifiedConfig:
    """

    Fixture providing a mock ManagerUnifiedConfig.
    """
    mock = MagicMock(spec=ManagerUnifiedConfig)
    mock.db = MagicMock()
    mock.volumes = {}
    mock.manager = MagicMock()
    return mock
