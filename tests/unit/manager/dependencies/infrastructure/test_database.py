from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.database import DatabaseDependency
from ai.backend.manager.errors.permission import GlobalEntityMissing

_LOADER = "ai.backend.manager.dependencies.infrastructure.database.GlobalEntityIDLoader"


class TestDatabaseDependency:
    """

    Test DatabaseDependency lifecycle.
    """

    @pytest.fixture
    def mock_config(self) -> ManagerUnifiedConfig:
        """

        Fixture providing a mock ManagerUnifiedConfig.
        """
        mock = MagicMock(spec=ManagerUnifiedConfig)
        mock.db = MagicMock()
        return mock

    @patch(_LOADER)
    @patch("ai.backend.manager.dependencies.infrastructure.database.connect_database")
    async def test_provide_database_engine(
        self,
        mock_connect_db: MagicMock,
        mock_loader: MagicMock,
        mock_config: ManagerUnifiedConfig,
    ) -> None:
        """

        Dependency should connect to database.
        """
        mock_engine = MagicMock()
        mock_loader.return_value.load = AsyncMock()

        @asynccontextmanager
        async def mock_context(config: ManagerUnifiedConfig) -> AsyncGenerator[MagicMock, None]:
            yield mock_engine

        mock_connect_db.return_value = mock_context(mock_config)

        dependency = DatabaseDependency()

        async with dependency.provide(mock_config) as db:
            assert db is mock_engine
            mock_connect_db.assert_called_once()
            mock_loader.assert_called_once_with(mock_engine)
            mock_loader.return_value.load.assert_awaited_once()

    @patch(_LOADER)
    @patch("ai.backend.manager.dependencies.infrastructure.database.connect_database")
    async def test_cleanup_on_exception(
        self,
        mock_connect_db: MagicMock,
        mock_loader: MagicMock,
        mock_config: ManagerUnifiedConfig,
    ) -> None:
        """

        Dependency should cleanup database connection even on exception.
        """
        mock_engine = MagicMock()
        mock_loader.return_value.load = AsyncMock()
        cleanup_called = False

        @asynccontextmanager
        async def mock_context(config: ManagerUnifiedConfig) -> AsyncGenerator[MagicMock, None]:
            nonlocal cleanup_called
            try:
                yield mock_engine
            finally:
                cleanup_called = True

        mock_connect_db.return_value = mock_context(mock_config)

        dependency = DatabaseDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(mock_config) as db:
                assert db is mock_engine
                raise RuntimeError("Test error")

        # Cleanup should have occurred
        assert cleanup_called is True

    @patch(_LOADER)
    @patch("ai.backend.manager.dependencies.infrastructure.database.connect_database")
    async def test_missing_global_entities_fail_startup(
        self,
        mock_connect_db: MagicMock,
        mock_loader: MagicMock,
        mock_config: ManagerUnifiedConfig,
    ) -> None:
        cleanup_called = False

        @asynccontextmanager
        async def mock_context(config: ManagerUnifiedConfig) -> AsyncGenerator[MagicMock, None]:
            nonlocal cleanup_called
            try:
                yield MagicMock()
            finally:
                cleanup_called = True

        mock_connect_db.return_value = mock_context(mock_config)
        mock_loader.return_value.load = AsyncMock(side_effect=GlobalEntityMissing())

        with pytest.raises(GlobalEntityMissing):
            async with DatabaseDependency().provide(mock_config):
                pytest.fail("The engine must not be provided.")

        assert cleanup_called is True
