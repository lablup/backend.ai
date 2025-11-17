from __future__ import annotations

from datetime import datetime, timezone

from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.types import (
    CID_POSTGRES,
    DATABASE,
    ComponentHealthStatus,
    ServiceGroup,
    ServiceHealth,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class DatabaseHealthChecker(StaticServiceHealthChecker):
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

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return DATABASE

    async def check_service(self) -> ServiceHealth:
        """
        Check database connection health by pinging the server.

        Returns:
            ServiceHealth containing status for postgres component
        """
        check_time = datetime.now(timezone.utc)

        try:
            await self._db.ping()
            status = ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        except Exception as e:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=str(e),
            )

        return ServiceHealth(results={CID_POSTGRES: status})

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
