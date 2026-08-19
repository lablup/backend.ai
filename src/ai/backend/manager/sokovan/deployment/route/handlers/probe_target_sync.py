"""Handler for syncing ReplicaProbeTargets to Valkey for active routes."""

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
    RouteStatusTransitions,
    RouteTargetStatuses,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class ReplicaProbeTargetSyncHandler(RouteHandler):
    """Periodically syncs ReplicaProbeTarget entries to Valkey for active routes.

    Targets RUNNING routes that have already been health-checked (HEALTHY,
    UNHEALTHY, DEGRADED). NOT_CHECKED routes are excluded intentionally —
    their probe targets are registered when they first transition to WARMING_UP.

    Covers two cases:
    - Valkey data lost (restart, eviction) → re-registers probe targets
    - TTL refresh for long-running routes that would otherwise expire
    """

    def __init__(self, route_executor: RouteExecutor) -> None:
        self._route_executor = route_executor

    @classmethod
    @override
    def name(cls) -> str:
        return "replica-probe-target-sync"

    @property
    @override
    def lock_id(self) -> LockID | None:
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
            health=[
                RouteHealthStatus.HEALTHY,
                RouteHealthStatus.UNHEALTHY,
                RouteHealthStatus.DEGRADED,
            ],
        )

    @classmethod
    @override
    def status_transitions(cls) -> RouteStatusTransitions:
        return RouteStatusTransitions(
            success=None,
            failure=None,
            stale=None,
        )

    @override
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Sync probe targets for routes that have health_check and replica info."""
        return await self._route_executor.sync_route_probe_targets(routes)

    @override
    async def post_process(self, result: RouteExecutionResult) -> None:
        if result.errors:
            log.warning(
                "Probe target sync: {} succeeded, {} failed",
                len(result.successes),
                len(result.errors),
            )
