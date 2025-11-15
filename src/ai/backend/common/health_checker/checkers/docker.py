from __future__ import annotations

from aiodocker import Docker

from ..abc import HealthChecker
from ..exceptions import DockerHealthCheckError


class DockerHealthChecker(HealthChecker):
    """
    Health checker for Docker connections.

    Uses the version() method of Docker to check connection health.
    """

    _docker: Docker
    _timeout: float

    def __init__(self, docker: Docker, timeout: float = 5.0) -> None:
        """
        Initialize DockerHealthChecker.

        Args:
            docker: The Docker client instance to check
            timeout: Timeout in seconds for the health check
        """
        self._docker = docker
        self._timeout = timeout

    async def check_health(self) -> None:
        """
        Check Docker connection health by getting version info.

        Raises:
            DockerHealthCheckError: If the version check fails
        """
        try:
            await self._docker.version()
        except Exception as e:
            raise DockerHealthCheckError(f"Docker health check failed: {e}") from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
