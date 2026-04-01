"""Handler for checking route health status."""

import logging
from collections.abc import Sequence

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
    RouteStatusTransitions,
    RouteTargetStatuses,
    RouteTransitionTarget,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class HealthCheckRouteHandler(RouteHandler):
    """Handler for checking route health status (readiness and liveness)."""

    def __init__(
        self,
        route_executor: RouteExecutor,
        event_producer: EventProducer,
    ) -> None:
        self._route_executor = route_executor
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "health-check-routes"

    @property
    def lock_id(self) -> LockID | None:
        """Lock for health check routes."""
        return LockID.LOCKID_DEPLOYMENT_HEALTH_CHECK_ROUTES

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.HEALTH

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.RUNNING],
            health=[
                RouteHealthStatus.NOT_CHECKED,
                RouteHealthStatus.HEALTHY,
                RouteHealthStatus.UNHEALTHY,
                RouteHealthStatus.DEGRADED,
            ],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Health check only changes health_status, not lifecycle status."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(health_status=RouteHealthStatus.HEALTHY),
            failure=RouteTransitionTarget(health_status=RouteHealthStatus.UNHEALTHY),
            stale=RouteTransitionTarget(health_status=RouteHealthStatus.DEGRADED),
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute health check for routes."""
        log.debug("Checking health for {} routes", len(routes))

        # Execute route health check logic via executor
        return await self._route_executor.check_route_health(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after health check."""
        log.debug(
            "Health check: {} healthy, {} unhealthy, {} degraded",
            len(result.successes),
            len(result.errors),
            len(result.stale),
        )
