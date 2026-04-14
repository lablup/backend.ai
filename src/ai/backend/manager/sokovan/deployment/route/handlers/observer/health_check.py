"""Observer for performing HTTP health checks on routes.

Reads RouteHealthRecord from Valkey, performs HTTP health checks in parallel,
and writes manager_healthy/manager_last_check back to Valkey.
During initial_delay, failures are ignored (not written).
The HealthCheckRouteHandler reads from Valkey and performs DB transitions.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

import aiohttp

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    RouteHealthRecord,
    ValkeyScheduleClient,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData

from .base import RouteObservationResult, RouteObserver

log = BraceStyleAdapter(logging.getLogger(__name__))

HEALTH_CHECK_TIMEOUT_SEC = 5


class RouteHealthObserver(RouteObserver):
    """Performs HTTP health checks on routes using RouteHealthRecord.

    Reads RouteHealthRecord from Valkey to get health_path, replica_host, inference_port.
    HTTP checks run in parallel via asyncio.gather.
    During initial_delay period, health check failures are ignored (not written to Valkey).
    After initial_delay, both success and failure results are written.
    """

    def __init__(
        self,
        deployment_repository: DeploymentRepository,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self._deployment_repository = deployment_repository
        self._valkey_schedule = valkey_schedule

    @classmethod
    def name(cls) -> str:
        return "route-health-observer"

    async def observe(self, routes: Sequence[RouteData]) -> RouteObservationResult:
        """Check health for routes using RouteHealthRecord from Valkey."""
        if not routes:
            return RouteObservationResult(observed_count=0)

        # Filter routes that have replica connection info
        checkable = [r for r in routes if r.replica_host and r.replica_port]
        if not checkable:
            return RouteObservationResult(observed_count=0)

        # Load RouteHealthRecords from Valkey
        route_ids = [str(r.route_id) for r in checkable]
        records = await self._valkey_schedule.get_route_health_records_batch(route_ids)

        # Collect routes that have records
        targets: list[tuple[str, RouteHealthRecord]] = []
        for route in checkable:
            route_id_str = str(route.route_id)
            record = records.get(route_id_str)
            if record is not None:
                targets.append((route_id_str, record))

        if not targets:
            if checkable:
                log.warning(
                    "Health observer: {} checkable routes but 0 have records in Valkey",
                    len(checkable),
                )
            return RouteObservationResult(observed_count=0)

        # Perform HTTP health checks in parallel
        check_tasks = [
            self._http_health_check(record.replica_host, record.inference_port, record.health_path)
            for _, record in targets
        ]
        results = await asyncio.gather(*check_tasks)

        # Write results to Valkey
        current_time = await self._valkey_schedule.get_redis_time()
        for (route_id_str, record), is_healthy in zip(targets, results, strict=False):
            within_initial_delay = current_time < record.initial_delay_until

            # Always refresh TTL to prevent key expiry
            await self._valkey_schedule.refresh_route_health_ttl(route_id_str)

            if is_healthy:
                await self._valkey_schedule.update_route_manager_health(route_id_str, True)
            elif not within_initial_delay:
                await self._valkey_schedule.update_route_manager_health(route_id_str, False)
            # else: failure within initial_delay → ignore (don't write)

        if targets:
            log.debug("Health observer: checked {} routes", len(targets))
        return RouteObservationResult(observed_count=len(targets))

    @staticmethod
    async def _http_health_check(host: str, port: int, path: str) -> bool:
        """Perform HTTP GET health check."""
        url = f"http://{host}:{port}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=HEALTH_CHECK_TIMEOUT_SEC)
                ) as resp:
                    return resp.status == 200
        except Exception:
            log.debug("Health check failed for {}", url)
            return False
