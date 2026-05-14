"""Handler for PROVISIONING+STARTING routes: checks host/port readiness."""

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
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class StartingRouteHandler(RouteHandler):
    """Checks if PROVISIONING+STARTING routes have replica host/port available.

    Success (→ WARMING_UP): session is running and host/port is populated.
    Failure (→ FAILED_TO_START): session terminated or not found.
    Routes running but without host/port yet are silently retried next tick.
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
        return "check-starting-routes"

    @property
    def lock_id(self) -> None:
        return None

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.PROVISIONING],
            sub_status=[RouteSubStatus.STARTING],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Host/port ready → sub_status=WARMING_UP; session dead → FAILED_TO_START."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                sub_status=RouteSubStatus.WARMING_UP,
            ),
            failure=RouteTransitionTarget(
                status=RouteStatus.TERMINATING,
            ),
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        log.debug("Checking {} starting routes for host/port readiness", len(routes))
        return await self._route_executor.check_starting_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        log.info(
            "Starting check: {} routes ready (→ warming_up), {} failed",
            len(result.successes),
            len(result.errors),
        )
