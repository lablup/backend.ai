"""Deployment strategy evaluator — orchestrates per-deployment FSM evaluation (BEP-1049).

Loads policies and routes in bulk, dispatches each deployment to the appropriate
strategy FSM, aggregates route mutations, and applies them in one batch.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentPolicyData,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.errors.deployment import (
    InvalidDeploymentStrategy,
    InvalidDeploymentStrategySpec,
)
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import BatchQuerier, Creator, NoPagination
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import RouteBatchUpdaterSpec
from ai.backend.manager.repositories.deployment.options import (
    DeploymentPolicyConditions,
    RouteConditions,
)
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .blue_green import blue_green_evaluate
from .rolling_update import rolling_update_evaluate
from .types import CycleEvaluationResult, EvaluationGroup, EvaluationResult

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentStrategyEvaluator:
    """Evaluates DEPLOYING deployments and produces grouped results + route mutations."""

    def __init__(self, deployment_repo: DeploymentRepository) -> None:
        self._deployment_repo = deployment_repo

    async def evaluate(
        self,
        deployments: Sequence[DeploymentInfo],
    ) -> EvaluationResult:
        """Evaluate all DEPLOYING deployments in a single cycle.

        Steps:
            1. Bulk-load policies and active routes.
            2. Per-deployment: dispatch to strategy FSM.
            3. Aggregate route changes and apply in one batch.
            4. Group deployments by sub-step and return.
        """
        result = EvaluationResult()

        if not deployments:
            return result

        endpoint_ids = {d.id for d in deployments}

        # ── 1. Bulk-load policies and routes ──
        policy_search = await self._deployment_repo.search_deployment_policies(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[DeploymentPolicyConditions.by_endpoint_ids(endpoint_ids)],
            )
        )
        policy_map = {p.endpoint: p for p in policy_search.items}
        route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(endpoint_ids)

        # ── 2. Per-deployment evaluation ──
        all_scale_out: list[Creator[RoutingRow]] = []
        all_scale_in_ids: list[UUID] = []

        for deployment in deployments:
            policy = policy_map.get(deployment.id)
            if policy is None:
                log.warning("deployment {}: no policy found — skipping", deployment.id)
                result.skipped.append(deployment)
                continue

            routes: list[RouteInfo] = list(route_map.get(deployment.id, []))

            try:
                cycle_result = self._evaluate_single(deployment, routes, policy.strategy, policy)
            except Exception as e:
                log.warning("deployment {}: evaluation error — {}", deployment.id, e)
                result.errors.append((deployment, str(e)))
                continue

            # Collect route changes
            changes = cycle_result.route_changes
            all_scale_out.extend(changes.scale_out_specs)
            all_scale_in_ids.extend(changes.scale_in_route_ids)

            # Group by sub-step
            if cycle_result.completed:
                result.completed.append(deployment)
                result.completed_strategies[deployment.id] = policy.strategy
            else:
                group = result.groups.setdefault(
                    cycle_result.sub_step,
                    EvaluationGroup(sub_step=cycle_result.sub_step),
                )
                group.deployments.append(deployment)

        # ── 3. Apply route mutations in batch ──
        await self._apply_route_changes(all_scale_out, all_scale_in_ids)

        return result

    def _evaluate_single(
        self,
        deployment: DeploymentInfo,
        routes: list[RouteInfo],
        strategy: DeploymentStrategy,
        policy: DeploymentPolicyData,
    ) -> CycleEvaluationResult:
        """Dispatch to the appropriate strategy FSM."""
        match strategy:
            case DeploymentStrategy.ROLLING:
                spec = policy.strategy_spec
                if not isinstance(spec, RollingUpdateSpec):
                    raise InvalidDeploymentStrategySpec(
                        extra_msg=f"Expected RollingUpdateSpec for ROLLING strategy, got {type(spec).__name__}"
                    )
                return rolling_update_evaluate(deployment, routes, spec)
            case DeploymentStrategy.BLUE_GREEN:
                spec = policy.strategy_spec
                if not isinstance(spec, BlueGreenSpec):
                    raise InvalidDeploymentStrategySpec(
                        extra_msg=f"Expected BlueGreenSpec for BLUE_GREEN strategy, got {type(spec).__name__}"
                    )
                return blue_green_evaluate(deployment, routes, spec)
            case _:
                raise InvalidDeploymentStrategy(
                    extra_msg=f"Unsupported deployment strategy: {strategy}"
                )

    async def _apply_route_changes(
        self,
        scale_out: list[Creator[RoutingRow]],
        scale_in_ids: list[UUID],
    ) -> None:
        """Apply aggregated route mutations in a single DB transaction."""
        if not scale_out and not scale_in_ids:
            return

        scale_in_updater: BatchUpdater[RoutingRow] | None = None
        if scale_in_ids:
            scale_in_updater = BatchUpdater(
                spec=RouteBatchUpdaterSpec(
                    status=RouteStatus.TERMINATING,
                    traffic_ratio=0.0,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                ),
                conditions=[RouteConditions.by_ids(scale_in_ids)],
            )

        await self._deployment_repo.scale_routes(scale_out, scale_in_updater)
        log.debug(
            "Applied route changes: {} created, {} terminated",
            len(scale_out),
            len(scale_in_ids),
        )
