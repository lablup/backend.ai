"""Observer for performing HTTP health checks on routes.

Checks routes that have not been checked recently (stale in Valkey)
and writes results back to Valkey. No DB state transitions are performed.
The HealthCheckRouteHandler reads from Valkey and performs DB transitions.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import aiohttp

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData

from .base import RouteObservationResult, RouteObserver

log = BraceStyleAdapter(logging.getLogger(__name__))

HEALTH_CHECK_TIMEOUT_SEC = 5


class RouteHealthObserver(RouteObserver):
    """Performs HTTP health checks on stale routes and writes results to Valkey.

    This is the manager fallback health checker. It only checks routes
    whose Valkey health data is missing or expired (stale).
    Routes must have replica_host and replica_port populated (set during provisioning).
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
        """Check health for routes with stale/missing Valkey data."""
        if not routes:
            return RouteObservationResult(observed_count=0)

        # Filter routes that have replica connection info
        checkable = [r for r in routes if r.replica_host and r.replica_port]
        if not checkable:
            return RouteObservationResult(observed_count=0)

        route_ids = [str(r.route_id) for r in checkable]

        # Find stale routes (no recent health data in Valkey)
        health_statuses = await self._valkey_schedule.check_route_health_status(route_ids)
        stale_routes = [r for r in checkable if health_statuses.get(str(r.route_id)) is None]

        if not stale_routes:
            return RouteObservationResult(observed_count=0)

        log.debug("Health observer: {} stale routes to check", len(stale_routes))

        # Resolve health check path from deployment revision
        health_paths = await self._resolve_health_paths(stale_routes)

        # Perform HTTP health checks and write to Valkey
        checked = 0
        for route in stale_routes:
            health_path = health_paths.get(route.route_id, "/health")
            is_healthy = await self._http_health_check(
                route.replica_host,
                route.replica_port,
                health_path,
            )
            await self._valkey_schedule.update_route_liveness(
                str(route.route_id),
                liveness=is_healthy,
            )
            checked += 1

        log.debug("Health observer: checked {} routes", checked)
        return RouteObservationResult(observed_count=checked)

    async def _resolve_health_paths(
        self,
        routes: Sequence[RouteData],
    ) -> dict[Any, str]:
        """Resolve health check path from revision's model_definition."""
        paths: dict[Any, str] = {}

        for route in routes:
            if route.revision_id in paths:
                continue
            # TODO: batch query revision model_definitions
            # For now, use default path
            paths[route.revision_id] = "/health"

        return {r.route_id: paths.get(r.revision_id, "/health") for r in routes}

    @staticmethod
    async def _http_health_check(host: str | None, port: int | None, path: str) -> bool:
        """Perform HTTP GET health check."""
        if not host or not port:
            return False
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
