from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.types import (
    REDIS,
    ComponentHealthStatus,
    ComponentId,
    ServiceGroup,
    ServiceHealth,
    SubComponentHealthStatus,
)


@runtime_checkable
class ValkeyPingable(Protocol):
    """Protocol for any client that supports ping() method."""

    async def ping(self) -> None:
        """Ping the server to check connection health."""
        ...


@runtime_checkable
class ValkeyOperationPingable(Protocol):
    """Protocol for clients that expose separate operation client health checks.

    Clients implementing this protocol (e.g., MonitoringValkeyClient) have
    independent operation and monitor sub-clients whose health can differ.
    """

    async def ping(self) -> None:
        """Ping the monitor client."""
        ...

    async def ping_operation_client(self) -> None:
        """Ping the operation client directly."""
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

    async def _ping_with_status(
        self,
        ping_coro: object,
        check_time: datetime,
    ) -> SubComponentHealthStatus:
        """
        Execute a ping coroutine and return a SubComponentHealthStatus.

        Args:
            ping_coro: An awaitable ping call
            check_time: The timestamp for the check
        """
        try:
            async with asyncio.timeout(self._component_timeout):
                await ping_coro  # type: ignore[misc]
            return SubComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        except TimeoutError:
            return SubComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"Timeout after {self._component_timeout}s",
            )
        except Exception as e:
            return SubComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=str(e),
            )

    async def _check_component(
        self,
        component_id: ComponentId,
        client: ValkeyPingable,
        check_time: datetime,
    ) -> tuple[ComponentId, ComponentHealthStatus]:
        """
        Check health of a single Valkey/Redis component with timeout.

        For clients implementing ValkeyOperationPingable (e.g., MonitoringValkeyClient),
        reports separate sub-component health for operation and monitor clients.

        Args:
            component_id: The component identifier
            client: The client to check
            check_time: The timestamp for the check

        Returns:
            Tuple of (component_id, status)
        """
        if isinstance(client, ValkeyOperationPingable):
            monitor_status, operation_status = await asyncio.gather(
                self._ping_with_status(client.ping(), check_time),
                self._ping_with_status(client.ping_operation_client(), check_time),
            )
            is_healthy = monitor_status.is_healthy and operation_status.is_healthy
            error_parts = []
            if not operation_status.is_healthy:
                error_parts.append(f"operation: {operation_status.error_message}")
            if not monitor_status.is_healthy:
                error_parts.append(f"monitor: {monitor_status.error_message}")
            status = ComponentHealthStatus(
                is_healthy=is_healthy,
                last_checked_at=check_time,
                error_message="; ".join(error_parts) if error_parts else None,
                sub_components={
                    "operation": operation_status,
                    "monitor": monitor_status,
                },
            )
        else:
            sub_status = await self._ping_with_status(client.ping(), check_time)
            status = ComponentHealthStatus(
                is_healthy=sub_status.is_healthy,
                last_checked_at=check_time,
                error_message=sub_status.error_message,
            )

        return (component_id, status)

    async def check_service(self) -> ServiceHealth:
        """
        Check health of all Valkey/Redis clients concurrently.

        Returns:
            ServiceHealth containing status for each component
        """
        check_time = datetime.now(UTC)

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
