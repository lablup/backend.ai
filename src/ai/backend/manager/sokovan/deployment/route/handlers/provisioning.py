"""Handler for provisioning routes."""

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


class ProvisioningRouteHandler(RouteHandler):
    """Handler for provisioning routes (PROVISIONING -> UNHEALTHY)."""

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
        return "provision-routes"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for provisioning routes."""
        return LockID.LOCKID_DEPLOYMENT_PROVISIONING_ROUTES

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.PROVISIONING]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """Get the next route status after this handler's operation."""
        return RouteStatus.UNHEALTHY

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """Get the failure route status if applicable."""
        return RouteStatus.FAILED_TO_START

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute provisioning for routes."""
        log.debug("Provisioning {} routes", len(routes))

        # Execute route provisioning logic via executor
        result = await self._route_executor.provision_routes(routes)
        return result

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after provisioning routes."""
        log.info(
            "Provisioned {} routes successfully, {} failed",
            len(result.successes),
            len(result.errors),
        )
