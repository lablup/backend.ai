from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.database import DatabaseDependency


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

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.infrastructure.database.connect_database")
    async def test_provide_database_engine(
        self, mock_connect_db: MagicMock, mock_config: ManagerUnifiedConfig
    ) -> None:
        """

        Dependency should connect to database.
        """
        mock_engine = MagicMock()

        @asynccontextmanager
        async def mock_context(config: ManagerUnifiedConfig):
            yield mock_engine

        mock_connect_db.return_value = mock_context(mock_config)

        dependency = DatabaseDependency()

        async with dependency.provide(mock_config) as db:
            assert db is mock_engine
            mock_connect_db.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.infrastructure.database.connect_database")
    async def test_cleanup_on_exception(
        self, mock_connect_db: MagicMock, mock_config: ManagerUnifiedConfig
    ) -> None:
        """

        Dependency should cleanup database connection even on exception.
        """
        mock_engine = MagicMock()
        cleanup_called = False

        @asynccontextmanager
        async def mock_context(config: ManagerUnifiedConfig):
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
