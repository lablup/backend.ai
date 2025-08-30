"""Handler for terminating routes."""

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


class TerminatingRouteHandler(RouteHandler):
    """Handler for terminating routes (TERMINATING -> TERMINATED)."""

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
        return "terminate-routes"

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for terminating routes."""
        return None

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.TERMINATING]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """Get the next route status after this handler's operation."""
        return RouteStatus.TERMINATED

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """Get the failure route status if applicable."""
        # Even if termination fails, we still mark as terminated
        return None

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute termination for routes."""
        log.debug("Terminating {} routes", len(routes))

        # Execute route termination logic via executor
        result = await self._route_executor.terminate_routes(routes)
        return result

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after terminating routes."""
        log.info(
            "Terminated {} routes successfully, {} failed",
            len(result.successes),
            len(result.errors),
        )
