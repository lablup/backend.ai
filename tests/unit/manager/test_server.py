"""Unit tests for server.py webapp plugin context."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

import ai.backend.manager.server as server_module
from ai.backend.manager.dependencies.composer import DependencyResources
from ai.backend.manager.server import webapp_plugin_ctx


@pytest.fixture
def mock_dependency_resources() -> DependencyResources:
    """Create a mock DependencyResources with required attributes."""
    mock_resources = MagicMock(spec=DependencyResources)

    # Mock bootstrap resources
    mock_bootstrap = MagicMock()
    mock_etcd = MagicMock()
    mock_config_provider = MagicMock()
    mock_config = MagicMock()
    mock_manager_config = MagicMock()

    mock_manager_config.allowed_plugins = []
    mock_manager_config.disabled_plugins = []
    mock_config.manager = mock_manager_config
    mock_config.model_dump = MagicMock(return_value={})
    mock_config_provider.config = mock_config

    mock_bootstrap.etcd = mock_etcd
    mock_bootstrap.config_provider = mock_config_provider
    mock_resources.bootstrap = mock_bootstrap

    # Mock infrastructure resources
    mock_infrastructure = MagicMock()
    mock_db = MagicMock()
    mock_infrastructure.db = mock_db
    mock_resources.infrastructure = mock_infrastructure

    # Mock system resources
    mock_system = MagicMock()
    mock_system.cors_options = {}
    mock_resources.system = mock_system

    return mock_resources


async def test_webapp_plugin_ctx_sets_db_and_config_provider(
    mock_dependency_resources: DependencyResources,
) -> None:
    """Test that webapp_plugin_ctx sets _db and _config_provider on the root app."""
    root_app = web.Application()

    # Mock the WebappPluginContext to avoid actual plugin loading
    mock_plugin_ctx = AsyncMock()
    mock_plugin_ctx.plugins = {}  # No plugins to load

    with patch.object(server_module, "WebappPluginContext", return_value=mock_plugin_ctx):
        async with webapp_plugin_ctx(
            root_app,
            dep_resources=mock_dependency_resources,
            pidx=0,
        ):
            # Verify that _db and _config_provider are set on root_app
            assert "_db" in root_app
            assert "_config_provider" in root_app
            assert root_app["_db"] is mock_dependency_resources.infrastructure.db
            assert (
                root_app["_config_provider"] is mock_dependency_resources.bootstrap.config_provider
            )
