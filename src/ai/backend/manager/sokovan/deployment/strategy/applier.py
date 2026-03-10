"""Applies strategy evaluation results (sub_step assignments + route mutations) to the DB."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentSubStep,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import RouteBatchUpdaterSpec
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .types import StrategyEvaluationSummary

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class StrategyApplyResult:
    """Result of applying a strategy evaluation to the database."""

    completed_ids: set[UUID] = field(default_factory=set)
    """Deployment IDs that completed and had their revision swapped."""

    rolled_back_ids: set[UUID] = field(default_factory=set)
    """Deployment IDs that rolled back and had their deploying_revision cleared."""

    routes_created: int = 0
    """Number of new routes rolled out."""

    routes_drained: int = 0
    """Number of routes marked for draining."""


class StrategyResultApplier:
    """Applies a ``StrategyEvaluationSummary`` to the database.

    Handles all DB mutations from a strategy evaluation cycle:
    1. Sub-step assignment updates
    2. Route rollout (create) and drain (terminate)
    3. Revision swap for COMPLETED deployments
    4. Clear deploying_revision for ROLLED_BACK deployments
    """

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        self._deployment_repo = deployment_repo

    async def apply(self, summary: StrategyEvaluationSummary) -> StrategyApplyResult:
        changes = summary.route_changes
        result = StrategyApplyResult(
            completed_ids=summary.assignments.get(DeploymentSubStep.COMPLETED, set()),
            rolled_back_ids=summary.assignments.get(DeploymentSubStep.ROLLED_BACK, set()),
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

        rollout: BulkCreator[RoutingRow] = BulkCreator(
            specs=[c.spec for c in changes.rollout_specs],
        )

        if summary.assignments or rollout.specs or drain:
            await self._deployment_repo.apply_strategy_evaluation(
                summary.assignments,
                rollout,
                drain,
            )
            log.debug(
                "Applied evaluation: {} sub_step groups, {} routes created, {} routes drained",
                len(summary.assignments),
                result.routes_created,
                result.routes_drained,
            )

        # Revision swap for completed deployments
        if result.completed_ids:
            swapped = await self._deployment_repo.complete_deployment_revision_swap(
                result.completed_ids
            )
            log.info(
                "Swapped revision for {}/{} completed deployments",
                swapped,
                len(result.completed_ids),
            )

        # Clear deploying_revision for rolled-back deployments
        if result.rolled_back_ids:
            await self._deployment_repo.clear_deploying_revision(result.rolled_back_ids)
            log.info(
                "Cleared deploying_revision for {} rolled-back deployments",
                len(result.rolled_back_ids),
            )

        return result
