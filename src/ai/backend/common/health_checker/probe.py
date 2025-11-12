from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from aiotools import cancel_and_wait

from ai.backend.common.dto.internal.health import ComponentHealthStatus, HealthCheckResponse

from .abc import HealthChecker
from .exceptions import HealthCheckerAlreadyRegistered, HealthCheckerNotFound
from .types import HealthCheckKey, HealthCheckStatus

log = logging.getLogger(__spec__.name)  # type: ignore[name-defined]


@dataclass
class HealthProbeOptions:
    """
    Configuration options for the health probe.
    """

    check_interval: float = 1.0


@dataclass
class RegisteredChecker:
    """
    Container for a registered health checker with its status.

    This is stored internally in the probe for each registered component.
    Combines the checker instance with runtime status.
    """

    checker: HealthChecker
    status: Optional[HealthCheckStatus] = None

    @property
    def current_status(self) -> Optional[HealthCheckStatus]:
        """
        Get the current health check status.

        Returns:
            The current health status, or None if no check has been performed yet
        """
        return self.status


class HealthProbe:
    """
    Probe for running periodic health checks on registered components.

    This class manages health checker registration and runs periodic checks
    on all registered components.
    """

    _checkers: dict[HealthCheckKey, RegisteredChecker]
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

    async def check_all(self) -> Mapping[HealthCheckKey, HealthCheckStatus]:
        """
        Check all registered health checkers immediately and return their statuses.

        This is useful for CLI tools or manual health checks.
        Updates the internal status registry with the results.

        Returns:
            A mapping from HealthCheckKey to HealthCheckStatus for all registered checkers
        """
        registered = await self._get_all_registered()
        now = datetime.now(timezone.utc)

        # Run all checks in parallel
        check_tasks = [self._check_single(key, reg.checker, now) for key, reg in registered.items()]
        statuses = await asyncio.gather(*check_tasks, return_exceptions=True)

        results: dict[HealthCheckKey, HealthCheckStatus] = {}
        for (key, _), status_or_exc in zip(registered.items(), statuses):
            if isinstance(status_or_exc, BaseException):
                log.error(
                    f"Unexpected error checking {key.service_group}/{key.component_id}: {status_or_exc}"
                )
                continue

            results[key] = status_or_exc
            # Update the status in registry
            try:
                await self._update_status(key, status_or_exc)
            except HealthCheckerNotFound:
                # Checker was unregistered while we were checking
                log.debug(
                    f"Checker unregistered during check: {key.service_group}/{key.component_id}"
                )

        return results

    async def register(
        self,
        key: HealthCheckKey,
        checker: HealthChecker,
    ) -> None:
        """
        Register a health checker for a specific component.

        Args:
            key: The key identifying the component (service_group + component_id)
            checker: The health checker instance

        Raises:
            HealthCheckerAlreadyRegistered: If a checker is already registered for this key
        """
        async with self._lock:
            if key in self._checkers:
                raise HealthCheckerAlreadyRegistered(
                    f"Health checker already registered for {key.service_group}/{key.component_id}"
                )
            self._checkers[key] = RegisteredChecker(
                checker=checker,
                status=None,
            )

    async def unregister(
        self,
        key: HealthCheckKey,
    ) -> None:
        """
        Unregister a health checker for a specific component.

        Args:
            key: The key identifying the component to unregister

        Raises:
            HealthCheckerNotFound: If no checker is registered for this key
        """
        async with self._lock:
            if key not in self._checkers:
                raise HealthCheckerNotFound(
                    f"No health checker registered for {key.service_group}/{key.component_id}"
                )
            del self._checkers[key]

    async def _get_all_registered(
        self,
    ) -> Mapping[HealthCheckKey, RegisteredChecker]:
        """
        Get all registered checkers with their configurations and statuses.

        Returns:
            A mapping from HealthCheckKey to RegisteredChecker
        """
        async with self._lock:
            return dict(self._checkers)

    async def _update_status(
        self,
        key: HealthCheckKey,
        status: HealthCheckStatus,
    ) -> None:
        """
        Update the health status of a specific component.

        Args:
            key: The key identifying the component to update
            status: The new health status

        Raises:
            HealthCheckerNotFound: If no checker is registered for this key
        """
        async with self._lock:
            if key not in self._checkers:
                raise HealthCheckerNotFound(
                    f"No health checker registered for {key.service_group}/{key.component_id}"
                )
            self._checkers[key].status = status

    async def _run_loop(self) -> None:
        """
        Main loop that periodically checks all registered checkers.

        This loop runs continuously, checking all registered checkers
        at the configured interval.
        Supports dynamic registration and unregistration.
        """
        log.debug(f"Health probe loop started (check interval: {self._options.check_interval}s)")

        while self._running:
            try:
                await asyncio.sleep(self._options.check_interval)
                await self.check_all()
            except asyncio.CancelledError:
                log.debug("Health probe loop cancelled")
                break
            except Exception as e:
                log.exception("Error in health probe loop: {}", e)
                # Continue running despite errors
        log.debug("Health probe loop stopped")

    async def _check_single(
        self,
        key: HealthCheckKey,
        checker: HealthChecker,
        check_time: datetime,
    ) -> HealthCheckStatus:
        """
        Execute a single health check.

        Args:
            key: The key identifying this checker
            checker: The health checker to execute
            check_time: The current time to record as check time

        Returns:
            The health check status result
        """
        service_group = key.service_group
        component_id = key.component_id

        try:
            # Run the health check with timeout
            await asyncio.wait_for(checker.check_health(), timeout=checker.timeout)

            # Health check succeeded
            status = HealthCheckStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
            log.debug(f"Health check succeeded for {service_group}/{component_id}")

        except asyncio.TimeoutError:
            # Health check timed out
            status = HealthCheckStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"Health check timed out after {checker.timeout}s",
            )
            log.warning(
                f"Health check timed out for {service_group}/{component_id} after {checker.timeout}s"
            )

        except Exception as e:
            # Health check failed with exception
            status = HealthCheckStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=str(e),
            )
            log.error(
                f"Health check failed for {service_group}/{component_id}: {e}",
                exc_info=True,
            )
        return status

    async def get_health_response(self) -> HealthCheckResponse:
        """
        Get the current health status as an API response.

        Converts internal health check statuses into a structured
        API response suitable for external consumption.

        Returns:
            HealthCheckResponse containing overall health and individual component statuses
        """
        registered = await self._get_all_registered()

        components = [
            ComponentHealthStatus(
                service_group=key.service_group,
                component_id=key.component_id,
                is_healthy=reg.status.is_healthy,
                last_checked_at=reg.status.last_checked_at,
                error_message=reg.status.error_message,
            )
            for key, reg in registered.items()
            if reg.status is not None
        ]
        overall_healthy = all(c.is_healthy for c in components) if components else True
        return HealthCheckResponse(
            overall_healthy=overall_healthy,
            components=components,
            timestamp=datetime.now(timezone.utc),
        )
