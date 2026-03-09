"""Deployment strategy evaluator — orchestrates per-deployment FSM evaluation (BEP-1049).

Loads policies and routes in bulk, dispatches each deployment to the appropriate
strategy FSM, and aggregates route mutations.  The evaluate handler is responsible
for applying the aggregated route changes and updating sub_step in DB.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentPolicyData,
    RouteInfo,
)
from ai.backend.manager.errors.deployment import (
    InvalidDeploymentStrategy,
    InvalidDeploymentStrategySpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.deployment.options import (
    DeploymentPolicyConditions,
)
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.recorder import DeploymentRecorderContext

from .types import (
    AbstractDeploymentStrategy,
    DeploymentStrategyRegistry,
    EvaluationResult,
    RouteChanges,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentStrategyEvaluator:
    """Evaluates DEPLOYING deployments and produces sub_step assignments + route mutations."""

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        strategy_registry: DeploymentStrategyRegistry,
    ) -> None:
        self._deployment_repo = deployment_repo
        self._strategy_registry = strategy_registry

    async def evaluate(
        self,
        deployments: Sequence[DeploymentInfo],
    ) -> EvaluationResult:
        """Evaluate all DEPLOYING deployments in a single cycle.

        Steps:
            1. Bulk-load policies and active routes.
            2. Per-deployment: dispatch to strategy FSM.
            3. Aggregate route changes and sub_step assignments.
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
        for deployment in deployments:
            policy = policy_map.get(deployment.id)
            if policy is None:
                log.warning("deployment {}: no policy found — skipping", deployment.id)
                continue

            routes: list[RouteInfo] = list(route_map.get(deployment.id, []))

            try:
                strategy = self._create_strategy(policy.strategy, policy)
                cycle_result = strategy.evaluate_cycle(deployment, routes)
            except Exception as e:
                log.warning("deployment {}: evaluation error — {}", deployment.id, e)
                continue

            # ── 3. Aggregate route changes and record sub-steps ──
            changes = cycle_result.route_changes
            result.route_changes.rollout_specs.extend(changes.rollout_specs)
            result.route_changes.drain_route_ids.extend(changes.drain_route_ids)
            self._record_route_changes(deployment, changes)

            # Classify into assignments
            result.assignments[cycle_result.sub_step].add(deployment.id)

        return result

    @staticmethod
    def _record_route_changes(deployment: DeploymentInfo, changes: RouteChanges) -> None:
        """Record rollout/drain operations as sub-steps for observability."""
        if not changes.rollout_specs and not changes.drain_route_ids:
            return
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)
        with recorder.phase("route_mutations"):
            if changes.rollout_specs:
                with recorder.step(
                    "rollout",
                    success_detail=f"{len(changes.rollout_specs)} new route(s)",
                ):
                    pass
            if changes.drain_route_ids:
                with recorder.step(
                    "drain",
                    success_detail=f"{len(changes.drain_route_ids)} route(s)",
                ):
                    pass

    def _create_strategy(
        self,
        strategy: DeploymentStrategy,
        policy: DeploymentPolicyData,
    ) -> AbstractDeploymentStrategy:
        """Create a strategy instance for the given deployment policy."""
        entry = self._strategy_registry.get(strategy)
        if entry is None:
            raise InvalidDeploymentStrategy(
                extra_msg=f"Unsupported deployment strategy: {strategy}"
            )
        spec = policy.strategy_spec
        if not isinstance(spec, entry.spec_type):
            raise InvalidDeploymentStrategySpec(
                extra_msg=(
                    f"Expected {entry.spec_type.__name__} for {strategy.name} strategy,"
                    f" got {type(spec).__name__}"
                ),
            )
        return entry.strategy_cls(spec)
