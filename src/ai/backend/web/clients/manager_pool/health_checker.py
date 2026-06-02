"""HealthProbe adapters for :class:`ManagerClientPool`.

Two checkers are split off because they serve different roles:

- :class:`ManagerPoolGateHealthChecker` emits a single ``pool`` component in
  the ``MANAGER`` service group with **any-healthy** semantics — it flips
  to unhealthy only when no endpoint is up. This is what the webserver
  readiness probe gates on (registered as a readiness checker).

- :class:`ManagerEndpointsHealthChecker` emits one component per endpoint
  in the ``MANAGER_ENDPOINTS`` service group. It is registered as
  *informational* so the per-endpoint results show up in the connectivity
  payload (``/health``) without affecting the readiness decision — which
  would otherwise require every endpoint to be healthy under the
  framework's all-components-must-be-healthy semantic per service group.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.health_checker.abc import ServiceHealthChecker
from ai.backend.common.health_checker.types import (
    MANAGER,
    ComponentHealthStatus,
    ComponentId,
    ServiceGroup,
    ServiceHealth,
)
from ai.backend.web.clients.endpoint_pool import HealthyEndpointPool

# Per-endpoint informational service group — not in any required set, so it
# emits to the connectivity payload without affecting readiness gating.
MANAGER_ENDPOINTS: ServiceGroup = ServiceGroup("manager-endpoints")

_DEFAULT_TIMEOUT = 1.0  # all checks read in-memory pool state, no I/O
_GATE_COMPONENT_ID: ComponentId = ComponentId("pool")


class ManagerPoolGateHealthChecker(ServiceHealthChecker):
    """Single ``pool`` component with any-healthy semantics — gates readiness."""

    _pool: HealthyEndpointPool
    _timeout: float

    def __init__(self, pool: HealthyEndpointPool, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._pool = pool
        self._timeout = timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        return MANAGER

    @property
    def timeout(self) -> float:
        return self._timeout

    async def check_service(self) -> ServiceHealth:
        has_healthy = self._pool.has_any_healthy()
        return ServiceHealth(
            results={
                _GATE_COMPONENT_ID: ComponentHealthStatus(
                    is_healthy=has_healthy,
                    last_checked_at=datetime.now(UTC),
                    error_message=None if has_healthy else "no healthy manager endpoint",
                ),
            },
        )


class ManagerEndpointsHealthChecker(ServiceHealthChecker):
    """Per-endpoint informational checker — does not gate any probe."""

    _pool: HealthyEndpointPool
    _timeout: float

    def __init__(self, pool: HealthyEndpointPool, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._pool = pool
        self._timeout = timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        return MANAGER_ENDPOINTS

    @property
    def timeout(self) -> float:
        return self._timeout

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
