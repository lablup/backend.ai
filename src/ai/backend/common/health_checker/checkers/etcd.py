from __future__ import annotations

from datetime import datetime, timezone

from ai.backend.common.etcd import AsyncEtcd

from ..abc import HealthChecker
from ..types import CID_ETCD, ETCD, HealthCheckResult, HealthCheckStatus, ServiceGroup


class EtcdHealthChecker(HealthChecker):
    """
    Health checker for etcd connections.

    Uses the ping() method of AsyncEtcd to check connection health.
    """

    _etcd: AsyncEtcd
    _timeout: float

    def __init__(self, etcd: AsyncEtcd, timeout: float = 5.0) -> None:
        """
        Initialize EtcdHealthChecker.

        Args:
            etcd: The etcd client instance to check
            timeout: Timeout in seconds for the health check
        """
        self._etcd = etcd
        self._timeout = timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return ETCD

    async def check_health(self) -> HealthCheckResult:
        """
        Check etcd connection health by pinging the server.

        Returns:
            HealthCheckResult containing status for etcd component
        """
        check_time = datetime.now(timezone.utc)

        try:
            await self._etcd.ping()
            status = HealthCheckStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        except Exception as e:
            status = HealthCheckStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=str(e),
            )

        return HealthCheckResult(results={CID_ETCD: status})

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
