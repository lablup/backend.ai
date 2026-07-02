"""Handler for evicting unhealthy routes based on scaling group configuration."""

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
    RouteStatusTransitions,
    RouteSubStatus,
    RouteTargetStatuses,
    RouteTransitionTarget,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult

from .base import RouteHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class RouteEvictionHandler(RouteHandler):
    """
    Handler for evicting routes that are no longer needed.

    Two eviction reasons are checked together:

    - **Health-based**: a RUNNING route whose health status is listed in
      the scaling group's ``cleanup_target_statuses`` (default: UNHEALTHY).
    - **Orphan revision**: an active (PROVISIONING / RUNNING) route whose
      ``revision_id`` belongs to neither the endpoint's ``current_revision``
      nor its ``deploying_revision``. This catches leftovers from a
      preempted rollout, regardless of endpoint lifecycle.
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
        """Get the name of the handler."""
        return "evict-routes"

    @property
    @override
    def lock_id(self) -> LockID | None:
        """No lock needed for eviction."""
        return None

    @classmethod
    @override
    def category(cls) -> RouteHandlerCategory:
        return RouteHandlerCategory.HEALTH

    @classmethod
    @override
    def target_statuses(cls) -> RouteTargetStatuses:
        # The handler runs over every active route (PROVISIONING / RUNNING)
        # regardless of health, because the orphan-revision check applies
        # to both lifecycle states. The scaling-group health policy still
        # filters to UNHEALTHY internally inside the executor.
        return RouteTargetStatuses(
            lifecycle=[RouteStatus.PROVISIONING, RouteStatus.RUNNING],
            health=list(RouteHealthStatus),
        )

    @classmethod
    @override
    def status_transitions(cls) -> RouteStatusTransitions:
        """Eviction: success → TERMINATING (draining stage), failure → no change."""
        return RouteStatusTransitions(
            success=RouteTransitionTarget(
                status=RouteStatus.TERMINATING,
                sub_status=RouteSubStatus.DRAINING,
            ),
            failure=None,
            stale=None,
        )

    @override
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Execute eviction for routes flagged by either eviction reason.

        Delegates to the executor, which combines the orphan-revision
        check with the scaling-group health policy in a single pass.
        """
        log.debug("Checking {} routes for eviction", len(routes))

        # Use executor logic to filter routes by scaling group config
        return await self._route_executor.cleanup_routes_by_config(routes)

    @override
    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after eviction check."""
        if result.successes:
            log.info(
                "Marked {} routes for eviction",
                len(result.successes),
            )
