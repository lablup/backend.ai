from __future__ import annotations

from datetime import datetime, timezone

from aiodocker import Docker

from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.types import (
    CID_DOCKER,
    CONTAINER,
    ComponentHealthStatus,
    ServiceGroup,
    ServiceHealth,
)


class DockerHealthChecker(StaticServiceHealthChecker):
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

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return CONTAINER

    async def check_service(self) -> ServiceHealth:
        """
        Check Docker connection health by getting version info.

        Returns:
            ServiceHealth containing status for docker component
        """
        check_time = datetime.now(timezone.utc)

        try:
            await self._docker.version()
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

        return ServiceHealth(results={CID_DOCKER: status})

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
