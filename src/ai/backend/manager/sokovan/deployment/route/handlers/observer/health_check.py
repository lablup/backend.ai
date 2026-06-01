"""Observer for performing HTTP health checks on routes.

Reads ReplicaProbeTarget from Valkey to get probe config (health_path, host, port),
performs HTTP health checks in parallel, and writes RouteHealthStatus back to Valkey.
The short TTL on RouteHealthStatus automatically signals DEGRADED on expiry.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

import aiohttp

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    ReplicaHealthResult,
    ValkeyScheduleClient,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData

from .base import RouteObservationResult, RouteObserver

log = BraceStyleAdapter(logging.getLogger(__name__))

HEALTH_CHECK_TIMEOUT_SEC = 5


class RouteHealthObserver(RouteObserver):
    """Performs HTTP health checks on routes using ReplicaProbeTarget from Valkey.

    Reads ReplicaProbeTarget (health_path, replica_host, inference_port) from Valkey.
    HTTP checks run in parallel via asyncio.gather.
    Writes RouteHealthStatus back to Valkey; TTL expiry signals DEGRADED automatically.
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
        """Check health for routes using ReplicaProbeTarget from Valkey."""
        if not routes:
            return RouteObservationResult(observed_count=0)

        # Load ReplicaProbeTargets from Valkey (keyed by ReplicaID)
        replica_ids = [r.route_id for r in routes]
        probe_targets = await self._valkey_schedule.get_route_probe_targets_batch(replica_ids)

        # Collect routes that have probe targets
        checkable = [
            (route, target)
            for route in routes
            if (target := probe_targets.get(route.route_id)) is not None
        ]

        if not checkable:
            if routes:
                log.warning(
                    "Health observer: {} routes but 0 have probe targets in Valkey",
                    len(routes),
                )
            return RouteObservationResult(observed_count=0)

        # Perform HTTP health checks in parallel
        check_tasks = [
            self._http_health_check(target.replica_host, target.inference_port, target.health_path)
            for _, target in checkable
        ]
        results = await asyncio.gather(*check_tasks)

        # Write results to Valkey in a single batch (TTL refreshed on every call)
        health_results = [
            ReplicaHealthResult(replica_id=route.route_id, healthy=is_healthy)
            for (route, _target), is_healthy in zip(checkable, results, strict=False)
        ]
        await self._valkey_schedule.record_route_health_statuses_batch(health_results)

        if checkable:
            log.debug("Health observer: checked {} routes", len(checkable))
        return RouteObservationResult(observed_count=len(checkable))

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
