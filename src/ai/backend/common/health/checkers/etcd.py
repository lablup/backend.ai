from __future__ import annotations

from ai.backend.common.etcd import AsyncEtcd

from ..abc import HealthChecker
from ..exceptions import EtcdHealthCheckError


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

    async def check_health(self) -> None:
        """
        Check etcd connection health by pinging the server.

        Raises:
            EtcdHealthCheckError: If the ping fails
        """
        try:
            await self._etcd.ping()
        except Exception as e:
            raise EtcdHealthCheckError(f"Etcd health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
