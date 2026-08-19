"""Handler for synchronizing ACTIVE routes to AppProxy."""

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
    RouteStatus,
    RouteStatusTransitions,
    RouteTargetStatuses,
    RouteTrafficStatus,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class AppProxySyncRouteHandler(RouteHandler):
    """Handler for syncing ACTIVE routes to the AppProxy.

    Targets RUNNING + traffic-ACTIVE routes regardless of health: sync
    reflects the manager's routing intent, while pruning unhealthy
    backends from the pool is AppProxy's own health-check responsibility.

    Single push-side entry point: API handlers and session lifecycle hooks
    no longer push directly. They mark APPPROXY_SYNC needed via
    RouteController, and the next route-coordinator cycle invokes this
    handler to call AppProxy's bulk routes-sync HTTP API once per proxy
    target — replacing the previous per-endpoint event + Redis hand-off.
    """

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
        return "appproxy-sync"

    @property
    @override
    def lock_id(self) -> LockID | None:
        # Sync is idempotent (set + event); the long cycle keeps state
        # convergent without an explicit distributed lock.
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
            traffic=[RouteTrafficStatus.ACTIVE],
        )

    @classmethod
    @override
    def status_transitions(cls) -> RouteStatusTransitions:
        # Pure side-effect handler; never mutates lifecycle/health columns.
        return RouteStatusTransitions(
            success=None,
            failure=None,
            stale=None,
        )

    @override
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        return await self._route_executor.sync_appproxy(routes)

    @override
    async def post_process(self, result: RouteExecutionResult) -> None:
        synced = len(result.successes)
        failed = len(result.errors)
        if failed:
            log.warning(
                "AppProxy sync complete: {} routes synced, {} routes failed",
                synced,
                failed,
            )
            for error in result.errors:
                log.warning(
                    "Failed to sync route {} to AppProxy: {}",
                    error.route_info.route_id,
                    error.reason,
                )
        else:
            log.trace("Successfully synced {} routes to AppProxy", synced)
