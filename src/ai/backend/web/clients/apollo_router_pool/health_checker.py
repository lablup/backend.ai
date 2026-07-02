"""HealthProbe adapters for the Apollo Router / Hive Gateway upstream.

Two checkers, mirroring the manager-side adapters:

- :class:`ApolloRouterPoolGateHealthChecker` — single ``pool`` component in
  the ``APOLLO_ROUTER`` service group with any-healthy semantics. Registered
  as a readiness checker so /readyz flips to 503 when no Apollo upstream is
  alive; the operator policy here is that a webserver without a working
  federation gateway should be considered unready even if manager traffic
  still flows.
- :class:`ApolloRouterEndpointsHealthChecker` — one component per endpoint in
  the ``APOLLO_ROUTER_ENDPOINTS`` service group, registered as
  *informational* so per-endpoint detail appears on /health without dragging
  readiness with it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from ai.backend.common.health_checker.abc import ServiceHealthChecker
from ai.backend.common.health_checker.types import (
    ComponentHealthStatus,
    ComponentId,
    ServiceGroup,
    ServiceHealth,
)
from ai.backend.web.clients.endpoint_pool import HealthyEndpointPool

APOLLO_ROUTER: ServiceGroup = ServiceGroup("apollo-router")
APOLLO_ROUTER_ENDPOINTS: ServiceGroup = ServiceGroup("apollo-router-endpoints")

_DEFAULT_TIMEOUT = 1.0
_GATE_COMPONENT_ID: ComponentId = ComponentId("pool")


class ApolloRouterPoolGateHealthChecker(ServiceHealthChecker):
    """Single ``pool`` component with any-healthy semantics — gates readiness."""

    _pool: HealthyEndpointPool
    _timeout: float

    def __init__(self, pool: HealthyEndpointPool, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._pool = pool
        self._timeout = timeout

    @property
    @override
    def target_service_group(self) -> ServiceGroup:
        return APOLLO_ROUTER

    @property
    @override
    def timeout(self) -> float:
        return self._timeout

    @override
    async def check_service(self) -> ServiceHealth:
        has_healthy = self._pool.has_any_healthy()
        return ServiceHealth(
            results={
                _GATE_COMPONENT_ID: ComponentHealthStatus(
                    is_healthy=has_healthy,
                    last_checked_at=datetime.now(UTC),
                    error_message=None if has_healthy else "no healthy apollo router endpoint",
                ),
            },
        )


class ApolloRouterEndpointsHealthChecker(ServiceHealthChecker):
    """Per-endpoint informational checker — does not gate any probe."""

    _pool: HealthyEndpointPool
    _timeout: float

    def __init__(self, pool: HealthyEndpointPool, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._pool = pool
        self._timeout = timeout

    @property
    @override
    def target_service_group(self) -> ServiceGroup:
        return APOLLO_ROUTER_ENDPOINTS

    @property
    @override
    def timeout(self) -> float:
        return self._timeout

    @override
    async def check_service(self) -> ServiceHealth:
        now = datetime.now(UTC)
        results: dict[ComponentId, ComponentHealthStatus] = {}
        for endpoint in self._pool.all_endpoints():
            healthy = self._pool.is_healthy(endpoint)
            results[ComponentId(endpoint)] = ComponentHealthStatus(
                is_healthy=healthy,
                last_checked_at=now,
                error_message=None if healthy else "endpoint unreachable",
            )
        return ServiceHealth(results=results)
