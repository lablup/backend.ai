"""Handler for synchronizing healthy routes to service discovery backend."""

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


class ServiceDiscoverySyncHandler(RouteHandler):
    """Handler for syncing healthy routes to service discovery backend."""

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
        return "service-discovery-sync"

    @property
    def lock_id(self) -> Optional[LockID]:
        """No lock needed for service discovery sync."""
        return None

    @classmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler."""
        return [RouteStatus.HEALTHY]

    @classmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """No status transition for service discovery sync."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """No failure status for service discovery sync."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[RouteStatus]:
        """Get the stale route status if applicable."""
        return None

    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute service discovery synchronization for healthy routes."""
        log.debug("Syncing {} healthy routes to service discovery", len(routes))

        # Execute service discovery sync logic via executor
        result = await self._route_executor.sync_service_discovery(routes)
        return result

    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after service discovery sync."""
        synced_count = len(result.successes)
        failed_count = len(result.errors)

        if failed_count > 0:
            log.warning(
                "Service discovery sync complete: {} synced, {} failed",
                synced_count,
                failed_count,
            )

            # Log details of failed syncs
            for error in result.errors:
                log.warning(
                    "Failed to sync route {} to service discovery: {}",
                    error.route_info.route_id,
                    error.reason,
                )
        else:
            log.trace("Successfully synced {} routes to service discovery", synced_count)
