"""Handler for running routes health check."""

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


class RunningRouteHandler(RouteHandler):
    """Handler for checking running routes (HEALTHY/UNHEALTHY)."""

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
        return "check-running-routes"

    @property
    def lock_id(self) -> LockID | None:
        """Lock for checking running routes."""
        return LockID.LOCKID_DEPLOYMENT_RUNNING_ROUTES

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.RUNNING, RouteStatus.FAILED_TO_START],
            health=list(RouteHealthStatus),
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Running check: success=no change, failure=TERMINATING (session died) + reset health."""
        return RouteStatusTransitions(
            success=None,
            failure=RouteTransitionTarget(
                status=RouteStatus.TERMINATING,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute health check for running routes."""
        log.debug("Checking health for {} running routes", len(routes))

        # Execute route health check logic via executor
        return await self._route_executor.check_running_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after checking running routes."""
        if result.errors:
            log.warning("Cleaning up {} routes", len(result.errors))
