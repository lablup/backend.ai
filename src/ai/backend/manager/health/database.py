from __future__ import annotations

from ai.backend.common.health_checker.abc import HealthChecker
from ai.backend.common.health_checker.exceptions import DatabaseHealthCheckError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class DatabaseHealthChecker(HealthChecker):
    """
    Health checker for database connections.

    Uses the ping() method of ExtendedAsyncSAEngine to check connection health.
    """

    _db: ExtendedAsyncSAEngine
    _timeout: float

    def __init__(self, db: ExtendedAsyncSAEngine, timeout: float = 5.0) -> None:
        """
        Initialize DatabaseHealthChecker.

        Args:
            db: The database engine instance to check
            timeout: Timeout in seconds for the health check
        """
        self._db = db
        self._timeout = timeout

    async def check_health(self) -> None:
        """
        Check database connection health by pinging the server.

        Raises:
            DatabaseHealthCheckError: If the ping fails
        """
        try:
            await self._db.ping()
        except Exception as e:
            raise DatabaseHealthCheckError(f"Database health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
