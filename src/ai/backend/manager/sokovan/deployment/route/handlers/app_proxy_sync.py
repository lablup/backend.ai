"""Handler for synchronizing healthy routes to App Proxy coordinator."""

import logging
from collections.abc import Sequence

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import RouteStatus, RouteStatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class AppProxySyncHandler(RouteHandler):
    """Handler for syncing healthy routes to App Proxy for traffic routing."""

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
        return "app-proxy-sync"

    @property
    def lock_id(self) -> LockID | None:
        """No lock needed for App Proxy sync."""
        return None

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.HEALTHY]

    @classmethod
    def next_status(cls) -> RouteStatus | None:
        """No status transition for App Proxy sync."""
        return None

    @classmethod
    def failure_status(cls) -> RouteStatus | None:
        """No failure status for App Proxy sync."""
        return None

    @classmethod
    def stale_status(cls) -> RouteStatus | None:
        """Get the stale route status if applicable."""
        return None

    @classmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Define state transitions for App Proxy sync handler.

        All transitions are None because this handler only syncs to App Proxy,
        it doesn't change route status.
        """
        return RouteStatusTransitions(
            success=None,
            failure=None,
            stale=None,
        )

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute App Proxy synchronization for healthy routes."""
        log.debug("Syncing {} healthy routes to App Proxy", len(routes))

        return await self._route_executor.sync_app_proxy(routes)

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after App Proxy sync."""
        synced_count = len(result.successes)
        failed_count = len(result.errors)

        if failed_count > 0:
            log.warning(
                "App Proxy sync complete: {} synced, {} failed",
                synced_count,
                failed_count,
            )

            for error in result.errors:
                log.warning(
                    "Failed to sync route {} to App Proxy: {}",
                    error.route_info.route_id,
                    error.reason,
                )
        else:
            log.trace("Successfully synced {} routes to App Proxy", synced_count)
