"""Handler for synchronizing healthy routes to service discovery backend."""

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.deployment.types import (
    RouteData,
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
    RouteStatusTransitions,
    RouteTargetStatuses,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = StructuredLogger(logging.getLogger(__name__))


class ServiceDiscoverySyncHandler(RouteHandler):
    """Handler for syncing healthy routes to service discovery backend."""

    def __init__(
        self,
        route_executor: RouteExecutor,
        event_producer: EventProducer,
    ) -> None:
        self._route_executor = route_executor
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> str:
        """Get the name of the handler."""
        return "service-discovery-sync"

    @property
    @override
    def lock_id(self) -> LockID | None:
        """No lock needed for service discovery sync."""
        return None

    @classmethod
    @override
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.SYNC

    @classmethod
    @override
    def target_statuses(cls) -> RouteTargetStatuses:
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.RUNNING],
            health=[RouteHealthStatus.HEALTHY],
        )

    @classmethod
    @override
    def status_transitions(cls) -> RouteStatusTransitions:
        """Define state transitions for service discovery sync handler (BEP-1030).

        All transitions are None because this handler only syncs to service discovery,
        it doesn't change route status.
        """
        return RouteStatusTransitions(
            success=None,
            failure=None,
            stale=None,
        )

    @override
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute service discovery synchronization for healthy routes."""
        # Execute service discovery sync logic via executor
        return await self._route_executor.sync_service_discovery(routes)

    @override
    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after service discovery sync."""
        synced_count = len(result.successes)
        failed_count = len(result.errors)

        if failed_count > 0:
            log.debug(
                "service discovery synced",
                success_count=synced_count,
                failure_count=failed_count,
            )
            for error in result.errors:
                log.warning(
                    "route service discovery sync failed",
                    route_id=error.route_info.route_id,
                    failure_reason=error.reason,
                )
        else:
            log.trace("service discovery synced", success_count=synced_count)
