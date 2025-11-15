from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..abc import HealthChecker
from ..exceptions import ValkeyHealthCheckError


@runtime_checkable
class ValkeyPingable(Protocol):
    """Protocol for any client that supports ping() method."""

    async def ping(self) -> None:
        """Ping the server to check connection health."""
        ...


class ValkeyHealthChecker(HealthChecker):
    """
    Health checker for Valkey/Redis connections.

    Accepts any client implementing the ValkeyPingable protocol
    (i.e., has a ping() method).
    """

    _client: ValkeyPingable
    _timeout: float

    def __init__(self, client: ValkeyPingable, timeout: float = 5.0) -> None:
        """
        Initialize ValkeyHealthChecker.

        Args:
            client: Any client instance with a ping() method
            timeout: Timeout in seconds for the health check
        """
        self._client = client
        self._timeout = timeout

    async def check_health(self) -> None:
        """
        Check Valkey connection health by pinging the server.

        Raises:
            ValkeyHealthCheckError: If the ping fails
        """
        try:
            await self._client.ping()
        except Exception as e:
            raise ValkeyHealthCheckError(f"Valkey health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
