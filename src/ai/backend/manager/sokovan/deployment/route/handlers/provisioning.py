"""Handler for provisioning routes."""

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


class ProvisioningRouteHandler(RouteHandler):
    """Handler for provisioning routes (PROVISIONING -> UNHEALTHY)."""

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
        return "provision-routes"

    @property
    def lock_id(self) -> LockID | None:
        """Lock for provisioning routes."""
        return LockID.LOCKID_DEPLOYMENT_PROVISIONING_ROUTES

    @classmethod
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.LIFECYCLE

    @classmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.PROVISIONING],
            health=list(RouteHealthStatus),
        )

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Provisioning → RUNNING + NOT_CHECKED on success, FAILED_TO_START on failure."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
            failure=RouteTransitionTarget(status=RouteStatus.FAILED_TO_START),
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute provisioning for routes."""
        log.debug("Provisioning {} routes", len(routes))

        # Execute route provisioning logic via executor
        return await self._route_executor.provision_routes(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after provisioning routes."""
        log.info(
            "Provisioned {} routes successfully, {} failed",
            len(result.successes),
            len(result.errors),
        )
