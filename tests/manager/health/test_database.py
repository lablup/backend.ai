from __future__ import annotations

import pytest
import sqlalchemy as sa

from ai.backend.common.health.exceptions import DatabaseHealthCheckError
from ai.backend.manager.health.database import DatabaseHealthChecker
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestDatabaseHealthChecker:
    """Test DatabaseHealthChecker with real database connections."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_success(self, database_engine: ExtendedAsyncSAEngine) -> None:
        """Test successful health check with real database connection."""
        checker = DatabaseHealthChecker(
            db=database_engine,
            timeout=5.0,
        )

        # Should not raise
        await checker.check_health()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_timeout_property(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = DatabaseHealthChecker(
            db=database_engine,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.integration
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
        await checker.check_health()
        await checker.check_health()
        await checker.check_health()

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

            with pytest.raises(DatabaseHealthCheckError) as exc_info:
                await checker.check_health()

            # Should contain error information
            assert "health check failed" in str(exc_info.value).lower()
        finally:
            await extended_engine.dispose()
