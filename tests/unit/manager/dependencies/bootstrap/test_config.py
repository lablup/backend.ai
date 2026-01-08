from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.logging.types import LogLevel
from ai.backend.manager.dependencies.bootstrap.config import (
    BootstrapConfigDependency,
    BootstrapConfigInput,
)


class TestBootstrapConfigDependency:
    """

    Test BootstrapConfigDependency lifecycle.
    """

    @pytest.mark.asyncio
    @patch("ai.backend.manager.config.bootstrap.BootstrapConfig.load_from_file")
    async def test_provide_config(self, mock_load_from_file: AsyncMock) -> None:
        """

        Dependency should load bootstrap config from file.
        """
        mock_config = MagicMock()
        mock_load_from_file.return_value = mock_config

        dependency = BootstrapConfigDependency()
        config_input = BootstrapConfigInput(
            config_path=Path("/test/config.toml"),
            log_level=LogLevel.INFO,
        )

        async with dependency.provide(config_input) as config:
            assert config is mock_config
            mock_load_from_file.assert_called_once_with(Path("/test/config.toml"), LogLevel.INFO)
