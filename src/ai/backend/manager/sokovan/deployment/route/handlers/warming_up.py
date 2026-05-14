"""Handler for PROVISIONING+WARMING_UP routes: initial health check to activate traffic."""

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
    RouteTrafficStatus,
    RouteTransitionTarget,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class WarmingUpRouteHandler(RouteHandler):
    """Runs initial health probe for PROVISIONING+WARMING_UP routes.

    Success (→ RUNNING+ACTIVE): health probe passes after initial_delay.
    Failed or still within initial_delay: no transition (route stays WARMING_UP, retried).
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
        return "check-warming-up-routes"

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
            sub_status=[RouteSubStatus.WARMING_UP],
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Health probe passes → RUNNING + HEALTHY + traffic=ACTIVE.
        Failure stays WARMING_UP (retry); expired/give_up → TERMINATING.
        """
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.RUNNING,
                traffic_status=RouteTrafficStatus.ACTIVE,
            ),
            failure=RouteTransitionTarget(
                status=RouteStatus.TERMINATING,
            ),
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        log.debug("Checking {} warming-up routes for initial health", len(routes))
        return await self._route_executor.check_warming_up_health(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        log.info(
            "Warming-up check: {} routes activated (→ running), {} still probing",
            len(result.successes),
            len(result.errors) + len(result.stale),
        )
