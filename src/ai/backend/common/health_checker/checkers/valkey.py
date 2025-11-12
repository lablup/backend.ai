from __future__ import annotations

from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient

from ..abc import HealthChecker
from ..exceptions import ValkeyHealthCheckError


class ValkeyHealthChecker(HealthChecker):
    """
    Health checker for Valkey/Redis connections.

    Uses the ping() method of AbstractValkeyClient to check connection health.
    """

    _client: AbstractValkeyClient
    _timeout: float

    def __init__(self, client: AbstractValkeyClient, timeout: float = 5.0) -> None:
        """
        Initialize ValkeyHealthChecker.

        Args:
            client: The Valkey client instance to check
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
