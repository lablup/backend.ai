from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine

from ai.backend.common.health.abc import HealthChecker
from ai.backend.common.health.exceptions import DatabaseHealthCheckError


class DatabaseHealthChecker(HealthChecker):
    """
    Health checker for database connections in App Proxy Coordinator.

    Uses a simple SELECT 1 query to check database connectivity.
    """

    _engine: AsyncEngine
    _timeout: float

    def __init__(self, engine: AsyncEngine, timeout: float = 5.0) -> None:
        """
        Initialize DatabaseHealthChecker.

        Args:
            engine: The database engine instance to check
            timeout: Timeout in seconds for the health check
        """
        self._engine = engine
        self._timeout = timeout

    async def check_health(self) -> None:
        """
        Check database connection health by executing a simple query.

        Raises:
            DatabaseHealthCheckError: If the query fails
        """
        try:
            async with self._engine.begin() as conn:
                await conn.scalar(sa.text("SELECT 1"))
        except Exception as e:
            raise DatabaseHealthCheckError(f"Database health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
