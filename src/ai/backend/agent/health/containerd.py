from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.types import (
    CID_CONTAINERD,
    CONTAINER,
    ComponentHealthStatus,
    ServiceGroup,
    ServiceHealth,
)


class ContainerdHealthChecker(StaticServiceHealthChecker):
    """
    Health checker for the containerd runtime connection.

    Lists containers over the gRPC channel as a lightweight liveness round-trip to the
    containerd daemon -- the containerd analogue of DockerHealthChecker's version() probe.
    Any successful response means the daemon is reachable; a channel/RPC error means it is not.
    """

    _runtime: OciRuntime
    _timeout: float

    def __init__(self, runtime: OciRuntime, timeout: float = 5.0) -> None:
        """
        Args:
            runtime: The containerd runtime whose gRPC connection is checked.
            timeout: Timeout in seconds for the health check.
        """
        self._runtime = runtime
        self._timeout = timeout

    @property
    @override
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return CONTAINER

    @override
    async def check_service(self) -> ServiceHealth:
        """Check containerd connection health with a lightweight container listing."""
        check_time = datetime.now(UTC)

        try:
            await self._runtime.list_containers()
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

        return ServiceHealth(results={CID_CONTAINERD: status})

    @property
    @override
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
