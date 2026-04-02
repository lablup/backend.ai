"""Handler for terminating routes."""

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


class TerminatingRouteHandler(RouteHandler):
    """Handler for terminating routes (TERMINATING -> TERMINATED)."""

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
        return "terminate-routes"

    @property
    def lock_id(self) -> LockID | None:
        """No lock needed for terminating routes."""
        return None

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.TERMINATING],
            health=list(RouteHealthStatus),
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Terminating → TERMINATED on success, reset health to NOT_CHECKED."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.TERMINATED,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
            failure=None,
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute termination for routes."""
        log.debug("Terminating {} routes", len(routes))

        # Execute route termination logic via executor
        return await self._route_executor.terminate_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after terminating routes."""
        log.info(
            "Terminated {} routes successfully, {} failed",
            len(result.successes),
            len(result.errors),
        )
