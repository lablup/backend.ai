"""Applies strategy evaluation results (sub_step assignments + route mutations) to the DB."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentLifecycleSubStep,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import RouteBatchUpdaterSpec
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .types import StrategyEvaluationSummary

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class StrategyApplyResult:
    """Result of applying a strategy evaluation to the database."""

    completed_ids: set[UUID] = field(default_factory=set)
    """Deployment IDs that completed and had their revision swapped."""

    routes_created: int = 0
    """Number of new routes rolled out."""

    routes_drained: int = 0
    """Number of routes marked for draining."""

    def has_mutations(self) -> bool:
        """Check if there are any route mutations to persist.

        Returns True when at least one of the following is present:
        new routes to roll out, routes to drain, or deployments completed.
        """
        return bool(self.completed_ids or self.routes_created or self.routes_drained)


class StrategyResultApplier:
    """Applies a ``StrategyEvaluationSummary`` to the database.

    Handles route mutations from a strategy evaluation cycle:
    1. Route rollout (create) and drain (terminate)
    2. Revision swap for COMPLETED deployments

    Sub-step transitions are handled exclusively by the coordinator.
    """

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        self._deployment_repo = deployment_repo

    async def apply(self, summary: StrategyEvaluationSummary) -> StrategyApplyResult:
        changes = summary.route_changes
        completed_ids: set[UUID] = set()
        for endpoint_id, sub_step in summary.assignments.items():
            if sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED:
                completed_ids.add(endpoint_id)

        result = StrategyApplyResult(
            completed_ids=completed_ids,
            routes_created=len(changes.rollout_specs),
            routes_drained=len(changes.drain_route_ids),
        )

        drain: BatchUpdater[RoutingRow] | None = None
        if changes.drain_route_ids:
            drain = BatchUpdater(
                spec=RouteBatchUpdaterSpec(
                    status=RouteStatus.TERMINATING,
                    traffic_ratio=0.0,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                ),
                conditions=[RouteConditions.by_ids(changes.drain_route_ids)],
            )

        rollout = changes.rollout_specs

        if not result.has_mutations():
            return result

        swapped = await self._deployment_repo.apply_strategy_mutations(
            rollout=rollout,
            drain=drain,
            completed_ids=completed_ids,
        )

        log.debug(
            "Applied evaluation: {} routes created, {} routes drained",
            result.routes_created,
            result.routes_drained,
        )
        if completed_ids:
            log.info(
                "Swapped revision for {}/{} completed deployments",
                swapped,
                len(completed_ids),
            )

        return result
