"""Handler for TERMINATING+DRAINING routes: remove traffic from AppProxy."""

import logging
from collections.abc import Sequence

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
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


class DrainingRouteHandler(RouteHandler):
    """Removes AppProxy traffic for routes entering termination.

    First stage of the TERMINATING pipeline (DRAINING → COOLING_DOWN):
    this stage only handles traffic removal; session cleanup happens in
    the COOLING_DOWN stage once the termination grace period elapses,
    counted from this stage's success transition.
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
        return "drain-routes"

    @property
    def lock_id(self) -> LockID | None:
        """No lock needed for draining routes."""
        return None

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.TERMINATING],
            sub_status=[RouteSubStatus.DRAINING],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Drained → COOLING_DOWN; the transition history timestamps the
        start of the termination grace period."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                sub_status=RouteSubStatus.COOLING_DOWN,
            ),
            failure=None,
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute traffic draining for routes.

        ``RouteExecutor.drain_routes`` pushes a synchronous AppProxy
        unregister; failures are logged but do not hold the route in
        DRAINING (the AppProxy sync handler converges leftovers).
        """
        log.debug("Draining {} routes", len(routes))
        return await self._route_executor.drain_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after draining routes."""
        log.info(
            "Drained {} routes (→ cooling down)",
            len(result.successes),
        )
