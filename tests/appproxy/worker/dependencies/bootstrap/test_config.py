from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.appproxy.worker.dependencies.bootstrap.config import (
    ConfigInput,
    ConfigProvider,
)


class TestConfigProvider:
    """Test ConfigProvider lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.appproxy.worker.dependencies.bootstrap.config.load")
    async def test_provide_config(self, mock_load: MagicMock) -> None:
        """Dependency should load config from file."""
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        dependency = ConfigProvider()
        config_input = ConfigInput(config_path=Path("/test/config.toml"))

        async with dependency.provide(config_input) as config:
            assert config is mock_config
            mock_load.assert_called_once_with(Path("/test/config.toml"))

    @pytest.mark.asyncio
    @patch("ai.backend.appproxy.worker.dependencies.bootstrap.config.load")
    async def test_provide_config_with_none_path(self, mock_load: MagicMock) -> None:
        """Dependency should handle None config path."""
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        dependency = ConfigProvider()
        config_input = ConfigInput(config_path=None)

        async with dependency.provide(config_input) as config:
            assert config is mock_config
            mock_load.assert_called_once_with(None)
