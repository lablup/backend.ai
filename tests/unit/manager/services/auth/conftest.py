"""Shared fixtures for auth service tests"""

from datetime import timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig, ManagerConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm


@pytest.fixture
def mock_hook_plugin_ctx() -> MagicMock:
    return MagicMock(spec=HookPluginContext)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.config = MagicMock(spec=ManagerConfig)
    mock_provider.config.auth = AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
        login_session_max_age=604800,
    )
    return mock_provider


@pytest.fixture
def sample_client_type_id() -> UUID:
    return uuid4()
