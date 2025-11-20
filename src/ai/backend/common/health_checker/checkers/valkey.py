from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from ..abc import StaticServiceHealthChecker
from ..types import REDIS, ComponentHealthStatus, ComponentId, ServiceGroup, ServiceHealth


@runtime_checkable
class ValkeyPingable(Protocol):
    """Protocol for any client that supports ping() method."""

    async def ping(self) -> None:
        """Ping the server to check connection health."""
        ...


class ValkeyHealthChecker(StaticServiceHealthChecker):
    """
    Health checker for Valkey/Redis connections.

    Checks multiple Valkey/Redis clients and returns health status for each component.
    Each client should implement the ValkeyPingable protocol (i.e., has a ping() method).
    """

    _clients: dict[ComponentId, ValkeyPingable]
    _timeout: float
    _component_timeout: float

    def __init__(
        self,
        clients: dict[ComponentId, ValkeyPingable],
        timeout: float = 5.0,
        component_timeout: float = 2.0,
    ) -> None:
        """
        Initialize ValkeyHealthChecker.

        Args:
            clients: Dictionary mapping ComponentId to client instances
                    (e.g., {ComponentId("artifact"): client1, ComponentId("live"): client2})
            timeout: Timeout in seconds for the entire health check (service group timeout)
            component_timeout: Timeout in seconds for each component's ping (should be < timeout)
        """
        self._clients = clients
        self._timeout = timeout
        self._component_timeout = component_timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return REDIS

    async def _check_component(
        self,
        component_id: ComponentId,
        client: ValkeyPingable,
        check_time: datetime,
    ) -> tuple[ComponentId, ComponentHealthStatus]:
        """
        Check health of a single Valkey/Redis component with timeout.

        Args:
            component_id: The component identifier
            client: The client to check
            check_time: The timestamp for the check

        Returns:
            Tuple of (component_id, status)
        """
        try:
            async with asyncio.timeout(self._component_timeout):
                await client.ping()
            status = ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        except asyncio.TimeoutError:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"Component timeout after {self._component_timeout}s",
            )
        except Exception as e:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=str(e),
            )

        return (component_id, status)

    async def check_service(self) -> ServiceHealth:
        """
        Check health of all Valkey/Redis clients concurrently.

        Returns:
            ServiceHealth containing status for each component
        """
        check_time = datetime.now(timezone.utc)

        # Run all health checks concurrently
        tasks = [
            self._check_component(component_id, client, check_time)
            for component_id, client in self._clients.items()
        ]

        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results: dict[ComponentId, ComponentHealthStatus] = {}
        for i, result in enumerate(check_results):
            if isinstance(result, BaseException):
                # This shouldn't happen since _check_component catches all exceptions,
                # but handle it just in case
                component_id = list(self._clients.keys())[i]
                results[component_id] = ComponentHealthStatus(
                    is_healthy=False,
                    last_checked_at=check_time,
                    error_message=f"Unexpected error: {result}",
                )
            else:
                comp_id, status = result
                results[comp_id] = status

        return ServiceHealth(results=results)

    @property
    def timeout(self) -> float:
        """The timeout for the entire health check in seconds."""
        return self._timeout
