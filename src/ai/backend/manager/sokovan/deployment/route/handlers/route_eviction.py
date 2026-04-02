"""Handler for evicting unhealthy routes based on scaling group configuration."""

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


class RouteEvictionHandler(RouteHandler):
    """
    Handler for evicting unhealthy routes based on scaling group configuration.

    This handler checks routes in UNHEALTHY state and marks them for
    termination if their status is in the scaling group's cleanup_target_statuses.
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
        return "evict-routes"

    @property
    def lock_id(self) -> LockID | None:
        """No lock needed for eviction."""
        return None

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.HEALTH

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.RUNNING],
            health=[RouteHealthStatus.UNHEALTHY],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Eviction: success → TERMINATING, failure → no change."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(status=RouteStatus.TERMINATING),
            failure=None,
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Execute eviction for unhealthy routes based on scaling group configuration.

        For each route, checks if its endpoint's scaling group has the route's current status
        in cleanup_target_statuses. If so, marks the route for termination.
        """
        log.debug("Checking {} routes for eviction", len(routes))

        # Use executor logic to filter routes by scaling group config
        return await self._route_executor.cleanup_routes_by_config(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after eviction check."""
        if result.successes:
            log.info(
                "Marked {} routes for eviction",
                len(result.successes),
            )
