"""Handler for checking route health status."""

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.model_serving.types import RouteStatus
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
    ):
        self._route_executor = route_executor
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "health-check-routes"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for health check routes."""
        return LockID.LOCKID_DEPLOYMENT_HEALTH_CHECK_ROUTES

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.HEALTHY, RouteStatus.UNHEALTHY]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """Routes that pass health check become HEALTHY."""
        return RouteStatus.HEALTHY

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """Routes that fail health check become UNHEALTHY."""
        return RouteStatus.UNHEALTHY

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute health check for routes."""
        log.debug("Checking health for {} routes", len(routes))

        # Execute route health check logic via executor
        result = await self._route_executor.check_route_health(routes)
        return result

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after health check."""
        healthy_count = len(result.successes)
        unhealthy_count = len(result.errors)

        if unhealthy_count > 0:
            log.debug(
                "Health check complete: {} healthy, {} unhealthy routes",
                healthy_count,
                unhealthy_count,
            )

            # Log details of unhealthy routes
            for error in result.errors:
                log.trace("Route {} is unhealthy: {}", error.route_info.route_id, error.reason)
        else:
            log.trace("All {} routes are healthy", healthy_count)
