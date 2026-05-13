"""Handler for warming-up routes (first health check gate)."""

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


class WarmingUpRouteHandler(RouteHandler):
    """Handler for warming-up routes (WARMING_UP -> RUNNING).

    A route enters WARMING_UP after its session has been provisioned but
    before traffic is allowed in. This handler decides when the route is
    ready to graduate:

    - When the endpoint has no health check configured, the route is
      considered ready as soon as its session is alive.
    - Otherwise, the route is held in WARMING_UP until the first healthy
      probe is observed in Valkey (written by ``RouteHealthObserver``).

    On readiness the route transitions to ``RUNNING`` + ``HEALTHY`` so
    the next ``AppProxySyncRouteHandler`` cycle picks it up for traffic
    routing. Sessions that died before becoming healthy fail to
    ``FAILED_TO_START``.
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
        return "warming-up-routes"

    @property
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_WARMING_UP_ROUTES

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.WARMING_UP],
            health=list(RouteHealthStatus),
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.HEALTHY,
            ),
            failure=RouteTransitionTarget(
                status=RouteStatus.FAILED_TO_START,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        log.debug("Evaluating {} warming-up routes", len(routes))
        return await self._route_executor.check_warming_up_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        log.info(
            "Warming-up: {} promoted to RUNNING, {} failed",
            len(result.successes),
            len(result.errors),
        )
