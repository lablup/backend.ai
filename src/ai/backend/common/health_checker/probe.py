from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from aiotools import cancel_and_wait

from ai.backend.common.dto.internal.health import (
    ComponentConnectivityStatus,
    HealthCheckResponse,
)
from ai.backend.logging.utils import BraceStyleAdapter

from .abc import HealthChecker
from .exceptions import HealthCheckerAlreadyRegistered, HealthCheckerNotFound
from .types import AllHealthCheckResults, HealthCheckResult, ServiceGroup

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HealthProbeOptions:
    """
    Configuration options for the health probe.
    """

    check_interval: float = 60.0


@dataclass
class RegisteredChecker:
    """
    Container for a registered health checker with its latest result.

    This is stored internally in the probe for each registered ServiceGroup.
    Combines the checker instance with runtime status containing results
    for multiple components within that service group.
    """

    checker: HealthChecker
    result: Optional[HealthCheckResult] = None

    @property
    def current_result(self) -> Optional[HealthCheckResult]:
        """
        Get the current health check result.

        Returns:
            The current health check result, or None if no check has been performed yet
        """
        return self.result


class HealthProbe:
    """
    Probe for running periodic health checks on registered service groups.

    This class manages health checker registration and runs periodic checks
    on all registered service groups. Each service group (e.g., REDIS, DATABASE, ETCD)
    has one health checker that checks multiple components within that group.
    """

    _checkers: dict[ServiceGroup, RegisteredChecker]
    _lock: asyncio.Lock
    _loop_task: Optional[asyncio.Task]
    _running: bool
    _options: HealthProbeOptions

    def __init__(self, options: HealthProbeOptions) -> None:
        """
        Initialize the health probe.

        Args:
            options: Configuration options for the probe
        """
        self._checkers = {}
        self._lock = asyncio.Lock()
        self._loop_task = None
        self._running = False
        self._options = options

    async def start(self) -> None:
        """
        Start the periodic health check loop.

        Creates a single background task that periodically checks all
        registered checkers and runs those whose interval has elapsed.
        Supports dynamic registration and unregistration of checkers.
        """
        if self._running:
            log.warning("Health probe is already running")
            return

        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        log.info("Started health probe")

    async def stop(self) -> None:
        """
        Stop the periodic health check loop.

        Cancels the background task and waits for it to complete.
        """
        if not self._running:
            log.warning("Health probe is not running")
            return

        self._running = False

        # Cancel the loop task
        if self._loop_task:
            await cancel_and_wait(self._loop_task)
            self._loop_task = None

        log.info("Stopped health probe")

    async def check_all(self) -> AllHealthCheckResults:
        """
        Check all registered health checkers immediately and return their results.

        This is useful for CLI tools or manual health checks.
        Updates the internal result registry with the results.

        Returns:
            AllHealthCheckResults containing results from all registered checkers
        """
        registered = await self._get_all_registered()
        now = datetime.now(timezone.utc)

        # Run all checks in parallel
        check_tasks = [
            self._check_single(service_group, reg.checker, now)
            for service_group, reg in registered.items()
        ]
        results_or_exc = await asyncio.gather(*check_tasks, return_exceptions=True)

        results: dict[ServiceGroup, HealthCheckResult] = {}
        for (service_group, _), result_or_exc in zip(registered.items(), results_or_exc):
            if isinstance(result_or_exc, BaseException):
                log.error(f"Unexpected error checking {service_group}: {result_or_exc}")
                continue

            results[service_group] = result_or_exc
            # Update the result in registry
            try:
                await self._update_result(service_group, result_or_exc)
            except HealthCheckerNotFound:
                # Checker was unregistered while we were checking
                log.debug(f"Checker unregistered during check: {service_group}")

        return AllHealthCheckResults(results=results)

    async def register(
        self,
        service_group: ServiceGroup,
        checker: HealthChecker,
    ) -> None:
        """
        Register a health checker for a specific service group.

        Args:
            service_group: The service group to register (e.g., REDIS, DATABASE, ETCD)
            checker: The health checker instance that checks all components in this service group

        Raises:
            HealthCheckerAlreadyRegistered: If a checker is already registered for this service group
        """
        async with self._lock:
            if service_group in self._checkers:
                raise HealthCheckerAlreadyRegistered(
                    f"Health checker already registered for {service_group}"
                )
            self._checkers[service_group] = RegisteredChecker(
                checker=checker,
                result=None,
            )

    async def unregister(
        self,
        service_group: ServiceGroup,
    ) -> None:
        """
        Unregister a health checker for a specific service group.

        Args:
            service_group: The service group to unregister

        Raises:
            HealthCheckerNotFound: If no checker is registered for this service group
        """
        async with self._lock:
            if service_group not in self._checkers:
                raise HealthCheckerNotFound(f"No health checker registered for {service_group}")
            del self._checkers[service_group]

    async def _get_all_registered(
        self,
    ) -> dict[ServiceGroup, RegisteredChecker]:
        """
        Get all registered checkers with their configurations and results.

        Returns:
            A mapping from ServiceGroup to RegisteredChecker
        """
        async with self._lock:
            return dict(self._checkers)

    async def _update_result(
        self,
        service_group: ServiceGroup,
        result: HealthCheckResult,
    ) -> None:
        """
        Update the health check result for a specific service group.

        Args:
            service_group: The service group to update
            result: The new health check result containing statuses for all components

        Raises:
            HealthCheckerNotFound: If no checker is registered for this service group
        """
        async with self._lock:
            if service_group not in self._checkers:
                raise HealthCheckerNotFound(f"No health checker registered for {service_group}")
            self._checkers[service_group].result = result

    async def _run_loop(self) -> None:
        """
        Main loop that periodically checks all registered checkers.

        This loop runs continuously, checking all registered checkers
        at the configured interval.
        Supports dynamic registration and unregistration.
        """
        log.debug(f"Health probe loop started (check interval: {self._options.check_interval}s)")

        try:
            while self._running:
                try:
                    await asyncio.sleep(self._options.check_interval)
                    await self.check_all()
                except Exception as e:
                    log.error(f"Error in health probe loop: {e}", exc_info=True)
                    # Continue running despite errors
        except asyncio.CancelledError:
            log.debug("Health probe loop cancelled")
            raise
        finally:
            log.debug("Health probe loop stopped")

    async def _check_single(
        self,
        service_group: ServiceGroup,
        checker: HealthChecker,
        check_time: datetime,
    ) -> HealthCheckResult:
        """
        Execute a single health check for a service group.

        Args:
            service_group: The service group being checked
            checker: The health checker to execute
            check_time: The current time to record as check time

        Returns:
            The health check result containing statuses for all components in this service group
        """
        try:
            # Run the health check with timeout
            result = await asyncio.wait_for(checker.check_health(), timeout=checker.timeout)
            log.debug(f"Health check succeeded for {service_group}")
            return result

        except asyncio.TimeoutError:
            # Health check timed out - return empty result
            log.warning(f"Health check timed out for {service_group} after {checker.timeout}s")
            return HealthCheckResult(results={})

        except Exception as e:
            # Health check failed with exception
            log.error(f"Health check failed for {service_group}: {e}", exc_info=True)
            return HealthCheckResult(results={})

    async def get_health_response(self) -> HealthCheckResponse:
        """
        Get the current health status as an API response.

        Converts internal health check results into a structured
        API response suitable for external consumption.
        Flattens component statuses from all service groups into a single list.

        Returns:
            HealthCheckResponse containing overall health and individual component statuses
        """
        registered = await self._get_all_registered()

        components: list[ComponentConnectivityStatus] = []
        for service_group, reg in registered.items():
            if reg.result is None:
                continue

            # Flatten component statuses from the result
            for component_id, status in reg.result.results.items():
                components.append(
                    ComponentConnectivityStatus(
                        service_group=service_group,
                        component_id=component_id,
                        is_healthy=status.is_healthy,
                        last_checked_at=status.last_checked_at,
                        error_message=status.error_message,
                    )
                )

        overall_healthy = all(c.is_healthy for c in components) if components else True
        return HealthCheckResponse(
            overall_healthy=overall_healthy,
            connectivity_checks=components,
            timestamp=datetime.now(timezone.utc),
        )
