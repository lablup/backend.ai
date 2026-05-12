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
from ai.backend.manager.repositories.deployment import DeploymentRepository
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
        deployment_repository: DeploymentRepository,
    ) -> None:
        self._route_executor = route_executor
        self._event_producer = event_producer
        self._deployment_repository = deployment_repository

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
        """Execute health check for routes.

        Revisions that opted out of ``service.health_check`` have no
        ``RouteHealthRecord`` in Valkey — including them would let the
        executor classify them as stale. Filter on the per-revision
        config fetched on entry so the probe loop only sees routes that
        should be probed.
        """
        log.debug("Checking health for {} routes", len(routes))
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])
        revision_ids = {r.revision_id for r in routes}
        hc_configs = await self._deployment_repository.fetch_health_check_configs(revision_ids)
        eligible = [r for r in routes if hc_configs.get(r.revision_id) is not None]
        if not eligible:
            return RouteExecutionResult(successes=[], errors=[])
        return await self._route_executor.check_route_health(eligible)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Log health-check results.

        ``RouteExecutor.check_route_health`` already pushed any
        first-time HEALTHY routes to AppProxy synchronously, so this
        handler is a thin logging shim — keeping ``post_process`` free
        of work whose failure must be tolerated.
        """
        log.debug(
            "Health check: {} healthy, {} unhealthy, {} degraded",
            len(result.successes),
            len(result.errors),
            len(result.stale),
        )
