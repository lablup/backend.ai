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
    RouteSubStatus,
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
    """Handler for terminating routes (TERMINATING+COOLING_DOWN → TERMINATED).

    Second stage of the TERMINATING pipeline: traffic was already removed
    in the DRAINING stage; this stage waits out each route's termination
    grace period and then cleans up the session.
    """

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
            sub_status=[RouteSubStatus.COOLING_DOWN],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Terminating → TERMINATED on success, reset health to NOT_CHECKED.

        Stale (still inside the termination grace period) has no target:
        the route stays COOLING_DOWN and is re-checked on the next cycle.
        """
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.TERMINATED,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
            failure=None,
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute termination for routes.

        ``RouteExecutor.terminate_routes`` destroys only the sessions
        whose termination grace period has elapsed, so this handler just
        delegates to it.
        """
        log.debug("Terminating {} routes", len(routes))
        return await self._route_executor.terminate_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after terminating routes."""
        log.info(
            "Terminated {} routes successfully, {} failed, {} cooling down",
            len(result.successes),
            len(result.errors),
            len(result.stale),
        )
