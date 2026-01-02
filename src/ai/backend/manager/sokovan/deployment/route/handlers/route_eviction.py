"""Handler for evicting unhealthy routes based on scaling group configuration."""

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import RouteStatus
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
    ):
        self._route_executor = route_executor
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "evict-routes"

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for eviction."""
        return None

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.UNHEALTHY]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """Routes that should be evicted become TERMINATING."""
        return RouteStatus.TERMINATING

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """No failure status for eviction - routes are either evicted or left as is."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[RouteStatus]:
        """No stale status for eviction handler."""
        return None

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
