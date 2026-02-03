from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.components.agent_cache import (
    AgentCacheDependency,
    AgentCacheInput,
)
from ai.backend.manager.dependencies.errors import InvalidManagerKeypairError


@dataclass
class MockManagerConfig:
    """Simple mock for manager config."""

    rpc_auth_manager_keypair: Path


@dataclass
class MockConfig:
    """Simple mock for config."""

    manager: MockManagerConfig


class TestAgentCacheDependency:
    """

    Test AgentCacheDependency lifecycle.
    """

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.agent_cache.load_certificate")
    @patch("ai.backend.manager.dependencies.components.agent_cache.AgentRPCCache")
    async def test_provide_agent_cache(
        self,
        mock_cache_class: MagicMock,
        mock_load_cert: MagicMock,
    ) -> None:
        """

        Dependency should create agent cache with manager keypair.
        """
        mock_load_cert.return_value = (b"public_key", b"secret_key")
        mock_cache = MagicMock()
        mock_cache_class.return_value = mock_cache

        db_engine = MagicMock()
        config = MockConfig(
            manager=MockManagerConfig(rpc_auth_manager_keypair=Path("/test/keypair"))
        )

        dependency = AgentCacheDependency()
        cache_input = AgentCacheInput(db=db_engine, config=config)  # type: ignore[arg-type]

        async with dependency.provide(cache_input) as agent_cache:
            assert agent_cache is mock_cache
            mock_load_cert.assert_called_once_with(Path("/test/keypair"))
            mock_cache_class.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.agent_cache.load_certificate")
    async def test_missing_secret_key_raises_error(
        self,
        mock_load_cert: MagicMock,
    ) -> None:
        """

        Dependency should raise error when secret key is missing.
        """
        mock_load_cert.return_value = (b"public_key", None)

        db_engine = MagicMock()
        config = MockConfig(
            manager=MockManagerConfig(rpc_auth_manager_keypair=Path("/test/keypair"))
        )

        dependency = AgentCacheDependency()
        cache_input = AgentCacheInput(db=db_engine, config=config)  # type: ignore[arg-type]

        with pytest.raises(
            InvalidManagerKeypairError,
            match="Manager secret key is missing from the keypair file",
        ):
            async with dependency.provide(cache_input):
                pass
