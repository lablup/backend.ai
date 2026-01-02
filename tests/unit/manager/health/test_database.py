from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa

from ai.backend.common.health_checker.types import CID_POSTGRES
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.bootstrap import DatabaseConfig
from ai.backend.manager.health.database import DatabaseHealthChecker
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, connect_database
from ai.backend.testutils.bootstrap import (  # noqa: F401
    HostPortPairModel,
)


@pytest.fixture
async def database_engine(
    postgres_container: tuple[str, HostPortPairModel],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """Create a database engine for testing."""
    container_id, postgres_addr = postgres_container
    db_config = DatabaseConfig(
        addr=HostPortPair(host=postgres_addr.host, port=postgres_addr.port),
        name="postgres",
        user="postgres",
        password="develove",
    )
    async with connect_database(db_config) as engine:
        yield engine


class TestDatabaseHealthChecker:
    """Test DatabaseHealthChecker with real database connections."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test successful health check with real database connection."""
        # Test the health checker - it uses ping() internally
        checker = DatabaseHealthChecker(
            db=database_engine,
            timeout=5.0,
        )

        # Should not raise - this tests actual DB connection
        await checker.check_service()

    @pytest.mark.asyncio
    async def test_timeout_property(self) -> None:
        """Test that timeout property returns the correct value."""
        # Create a dummy engine (won't be used for actual connection)
        dummy_engine = sa.ext.asyncio.create_async_engine(
            "postgresql+asyncpg://invalid:invalid@localhost:99999/invalid",
            echo=False,
        )
        extended_engine = ExtendedAsyncSAEngine(dummy_engine)

        try:
            timeout_value = 3.5
            checker = DatabaseHealthChecker(
                db=extended_engine,
                timeout=timeout_value,
            )

            assert checker.timeout == timeout_value
        finally:
            await extended_engine.dispose()

    @pytest.mark.asyncio
    async def test_multiple_checks(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that multiple health checks work correctly."""
        checker = DatabaseHealthChecker(
            db=database_engine,
            timeout=5.0,
        )

        # Multiple checks should all succeed
        await checker.check_service()
        await checker.check_service()
        await checker.check_service()

    @pytest.mark.asyncio
    async def test_invalid_connection(self) -> None:
        """Test health check failure with invalid database connection."""
        # Create engine with invalid connection string
        invalid_engine = sa.ext.asyncio.create_async_engine(
            "postgresql+asyncpg://invalid:invalid@localhost:99999/invalid",
            echo=False,
        )

        # Wrap in ExtendedAsyncSAEngine
        extended_engine = ExtendedAsyncSAEngine(invalid_engine)

        try:
            checker = DatabaseHealthChecker(
                db=extended_engine,
                timeout=2.0,
            )

            # check_service returns unhealthy status instead of raising exception
            result = await checker.check_service()

            # Should return unhealthy status with error message
            assert CID_POSTGRES in result.results
            status = result.results[CID_POSTGRES]
            assert not status.is_healthy
            assert status.error_message is not None
        finally:
            await extended_engine.dispose()
