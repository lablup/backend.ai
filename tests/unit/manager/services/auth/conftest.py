"""Shared fixtures for auth service tests"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig, ManagerConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm


@pytest.fixture
def mock_hook_plugin_ctx():
    return MagicMock(spec=HookPluginContext)


@pytest.fixture
def mock_config_provider():
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.config = MagicMock(spec=ManagerConfig)
    mock_provider.config.auth = AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
    )
    return mock_provider
