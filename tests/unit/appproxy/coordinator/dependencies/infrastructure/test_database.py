from __future__ import annotations

from unittest.mock import Mock

import pytest
import sqlalchemy as sa

from ai.backend.appproxy.coordinator.config import (
    DBConfig,
    ServerConfig,
)
from ai.backend.appproxy.coordinator.dependencies.infrastructure.database import (
    DatabaseProvider,
)
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestDatabaseProvider:
    """Test DatabaseProvider with real database container."""

    @pytest.fixture
    def coordinator_db_config(
        self,
        postgres_container: tuple[str, HostPortPairModel],
    ) -> ServerConfig:
        """Create a coordinator config pointing to the test database."""
        from ai.backend.appproxy.common.config import HostPortPair
        from ai.backend.appproxy.coordinator.config import DBType

        container_id, db_addr = postgres_container

        # Create DB config for testing
        db_config = DBConfig(
            type=DBType.POSTGRESQL,
            addr=HostPortPair(host=db_addr.host, port=db_addr.port),
            name="testing",
            user="postgres",
            password="develove",
            pool_size=8,
            max_overflow=64,
        )

        config = Mock(spec=ServerConfig)
        config.db = db_config
        return config

    @pytest.mark.asyncio
    async def test_provide_database_engine(
        self,
        coordinator_db_config: ServerConfig,
    ) -> None:
        """Dependency should create and cleanup database engine."""
        dependency = DatabaseProvider()

        async with dependency.provide(coordinator_db_config) as db:
            assert db is not None
            # Verify the engine is functional by testing a simple query
            async with db.connect() as conn:
                result = await conn.scalar(sa.text("SELECT 1"))
                assert result == 1

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        coordinator_db_config: ServerConfig,
    ) -> None:
        """Dependency should cleanup database engine even on exception."""
        dependency = DatabaseProvider()

        with pytest.raises(RuntimeError):
            async with dependency.provide(coordinator_db_config) as db:
                assert db is not None
                raise RuntimeError("Test error")

        # Engine should be closed - we can't easily verify this,
        # but the test should complete without hanging
