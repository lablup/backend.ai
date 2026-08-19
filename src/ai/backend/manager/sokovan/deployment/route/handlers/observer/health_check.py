"""Observer for performing HTTP health checks on routes.

Reads ReplicaProbeTarget from Valkey to get probe config (health_path, host, port),
performs HTTP health checks in parallel, and writes RouteHealthStatus back to Valkey.
The short TTL on RouteHealthStatus automatically signals DEGRADED on expiry.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import aiohttp

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    ReplicaHealthResult,
    ReplicaProbeTarget,
    ValkeyScheduleClient,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData

from .base import RouteObservationResult, RouteObserver

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class _ProbePlan:
    """A route selected for probing this tick, with the prior failure count."""

    route_id: ReplicaID
    target: ReplicaProbeTarget
    health_check: ModelHealthCheck
    prev_failures: int


class RouteHealthObserver(RouteObserver):
    """Performs HTTP health checks on routes using ReplicaProbeTarget from Valkey.

    Reads ReplicaProbeTarget (health_path, replica_host, inference_port) from Valkey
    for the endpoint, and per-route policy (interval, max_wait_time,
    expected_status_code) from ``RouteData.health_check``.

    Per route the observer throttles to the configured ``interval``, runs the HTTP
    probe with ``max_wait_time`` / ``expected_status_code``, and accumulates a
    ``consecutive_failures`` counter (reset to 0 on a passing probe) in Valkey.
    It only counts; the RUNNING health-check handler compares the counter against
    ``max_retries`` to decide UNHEALTHY. TTL expiry signals DEGRADED automatically.
    """

    def __init__(
        self,
        deployment_repository: DeploymentRepository,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self._deployment_repository = deployment_repository
        self._valkey_schedule = valkey_schedule

    @classmethod
    @override
    def name(cls) -> str:
        return "route-health-observer"

    @override
    async def observe(self, routes: Sequence[RouteData]) -> RouteObservationResult:
        """Check health for routes using ReplicaProbeTarget from Valkey."""
        if not routes:
            return RouteObservationResult(observed_count=0)

        # Load probe targets (endpoint), prior statuses (count + last_check), and the
        # current time in one round-trip — the three reads are independent.
        replica_ids = [r.route_id for r in routes]
        probe_targets, prev_statuses, now = await asyncio.gather(
            self._valkey_schedule.get_route_probe_targets_batch(replica_ids),
            self._valkey_schedule.get_route_health_statuses_batch(replica_ids),
            self._valkey_schedule.get_redis_time(),
        )

        # Select routes that have a probe target and are due for a probe (interval throttle).
        # A probe target only exists when health_check is set (see _build_probe_target),
        # so health_check is non-None for every selected route.
        plans: list[_ProbePlan] = []
        for route in routes:
            target = probe_targets.get(route.route_id)
            health_check = route.enabled_health_check
            if target is None or health_check is None:
                continue
            prev = prev_statuses.get(route.route_id)
            if prev is not None and not health_check.is_probe_due(prev.last_check, now):
                continue
            plans.append(
                _ProbePlan(
                    route_id=route.route_id,
                    target=target,
                    health_check=health_check,
                    prev_failures=prev.consecutive_failures if prev is not None else 0,
                )
            )

        if not plans:
            return RouteObservationResult(observed_count=0)

        # Perform HTTP health checks in parallel using per-route policy.
        results = await asyncio.gather(*[
            self._http_health_check(
                plan.target.replica_host,
                plan.target.inference_port,
                plan.target.health_path,
                plan.health_check.max_wait_time,
                plan.health_check.expected_status_code,
            )
            for plan in plans
        ])

        # Increment/reset consecutive_failures; record with per-route interval-based TTL.
        health_results = [
            ReplicaHealthResult(
                replica_id=plan.route_id,
                healthy=is_healthy,
                consecutive_failures=0 if is_healthy else plan.prev_failures + 1,
                ttl_sec=plan.health_check.health_status_ttl_sec(),
            )
            for plan, is_healthy in zip(plans, results, strict=False)
        ]
        await self._valkey_schedule.record_route_health_statuses_batch(health_results)

        log.debug("Health observer: checked {} routes", len(plans))
        return RouteObservationResult(observed_count=len(plans))

    @staticmethod
    async def _http_health_check(
        host: str,
        port: int,
        path: str,
        max_wait_time: float,
        expected_status_code: int,
    ) -> bool:
        """Perform HTTP GET health check."""
        url = f"http://{host}:{port}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=max_wait_time)
                ) as resp:
                    return resp.status == expected_status_code
        except Exception:
            log.debug("Health check failed for {}", url)
            return False
