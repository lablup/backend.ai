"""Handler for running routes health check."""

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


class RunningRouteHandler(RouteHandler):
    """Handler for checking running routes (HEALTHY/UNHEALTHY)."""

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
        return "check-running-routes"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for checking running routes."""
        return LockID.LOCKID_DEPLOYMENT_RUNNING_ROUTES

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.HEALTHY, RouteStatus.UNHEALTHY, RouteStatus.FAILED_TO_START]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        return None

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """Get the failure route status if applicable."""
        return RouteStatus.TERMINATING

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute health check for running routes."""
        log.debug("Checking health for {} running routes", len(routes))

        # Execute route health check logic via executor
        result = await self._route_executor.check_running_routes(routes)
        return result

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after checking running routes."""
        if result.errors:
            log.warning("Cleaning up {} routes", len(result.errors))
