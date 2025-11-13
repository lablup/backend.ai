from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.components.agent_cache import (
    AgentCacheDependency,
    AgentCacheInput,
)
from ai.backend.manager.dependencies.errors import InvalidManagerKeypairError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestAgentCacheDependency:
    """

    Test AgentCacheDependency lifecycle.
    """

    @pytest.mark.asyncio
    async def test_stage_name(self) -> None:
        """

        Dependency should have correct stage name.
        """
        dependency = AgentCacheDependency()
        assert dependency.stage_name == "agent-cache"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.agent_cache.load_certificate")
    @patch("ai.backend.manager.dependencies.components.agent_cache.AgentRPCCache")
    async def test_provide_agent_cache(
        self,
        mock_cache_class: MagicMock,
        mock_load_cert: MagicMock,
        mock_db_engine: ExtendedAsyncSAEngine,
        mock_config: ManagerUnifiedConfig,
    ) -> None:
        """

        Dependency should create agent cache with manager keypair.
        """
        mock_load_cert.return_value = (b"public_key", b"secret_key")
        mock_cache = MagicMock()
        mock_cache_class.return_value = mock_cache

        mock_config.manager.rpc_auth_manager_keypair = Path("/test/keypair")

        dependency = AgentCacheDependency()
        cache_input = AgentCacheInput(db=mock_db_engine, config=mock_config)

        async with dependency.provide(cache_input) as agent_cache:
            assert agent_cache is mock_cache
            mock_load_cert.assert_called_once_with(Path("/test/keypair"))
            mock_cache_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.agent_cache.load_certificate")
    async def test_missing_secret_key_raises_error(
        self,
        mock_load_cert: MagicMock,
        mock_db_engine: ExtendedAsyncSAEngine,
        mock_config: ManagerUnifiedConfig,
    ) -> None:
        """

        Dependency should raise error when secret key is missing.
        """
        mock_load_cert.return_value = (b"public_key", None)
        mock_config.manager.rpc_auth_manager_keypair = Path("/test/keypair")

        dependency = AgentCacheDependency()
        cache_input = AgentCacheInput(db=mock_db_engine, config=mock_config)

        with pytest.raises(
            InvalidManagerKeypairError,
            match="Manager secret key is missing from the keypair file",
        ):
            async with dependency.provide(cache_input):
                pass
