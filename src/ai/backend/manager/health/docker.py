from __future__ import annotations

from aiodocker import Docker

from ai.backend.common.health.abc import HealthChecker
from ai.backend.common.health.exceptions import DockerHealthCheckError


class DockerHealthChecker(HealthChecker):
    """
    Health checker for Docker daemon connectivity.

    Uses aiodocker to check if the Docker daemon is accessible and responsive.
    The Docker client instance is reused across multiple health checks.
    """

    _docker: Docker
    _timeout: float

    def __init__(self, timeout: float = 5.0) -> None:
        """
        Initialize DockerHealthChecker.

        Args:
            timeout: Timeout in seconds for the health check
        """
        self._docker = Docker()
        self._timeout = timeout

    async def check_health(self) -> None:
        """
        Check Docker daemon health by getting version information.

        Raises:
            DockerHealthCheckError: If the Docker daemon is not accessible
        """
        try:
            await self._docker.version()
        except Exception as e:
            raise DockerHealthCheckError(f"Docker health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout

    async def close(self) -> None:
        """Close the Docker client connection."""
        await self._docker.close()
