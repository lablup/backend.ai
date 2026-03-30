"""Rolling update strategy evaluation for a single deployment cycle (BEP-1049).

Classifies routes by revision (old/new) and status, then decides the next
sub-step and route mutations based on ``max_surge`` / ``max_unavailable``.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    RouteInfo,
    RouteStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.deployment_policy import DeploymentStrategySpec, RollingUpdateSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.exceptions import InvalidEndpointState

from .types import AbstractDeploymentStrategy, RouteChanges, StrategyCycleResult

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class _ClassifiedRoutes:
    """Routes classified by revision and status.

    Only ``old_active`` retains full RouteInfo (needed for drain ordering).
    Other buckets store counts only.
    """

    old_active: list[RouteInfo] = field(default_factory=list)
    new_provisioning_count: int = 0
    new_healthy_count: int = 0
    new_unhealthy_count: int = 0
    new_failed_count: int = 0

    @property
    def total_new_running(self) -> int:
        """Count of new-revision routes whose processes are still running.

        Includes UNHEALTHY and DEGRADED to prevent duplicate route creation
        in surge calculation.  (They are excluded from ``available_count``
        in termination calculation, since they cannot serve traffic.)
        """
        return self.new_provisioning_count + self.new_healthy_count + self.new_unhealthy_count


class RollingUpdateStrategy(AbstractDeploymentStrategy):
    """Rolling update deployment strategy FSM."""

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
        spec: DeploymentStrategySpec,
    ) -> StrategyCycleResult:
        """Evaluate one cycle of rolling update for a single deployment.

        FSM flow:
            1. Classify routes into old / new by revision_id.
            2. If any new route is PROVISIONING → PROVISIONING (wait).
            3. If no old routes remain and new_healthy >= desired → COMPLETED.
            4. Compute allowed surge/unavailable, decide create/terminate
               → PROVISIONING (with route mutations).

        Rollback is not decided by the FSM — the coordinator's timeout
        sweep handles it by transitioning to ROLLING_BACK when the
        deploying timeout is exceeded.
        """
        if not isinstance(spec, RollingUpdateSpec):
            raise TypeError(f"Expected RollingUpdateSpec, got {type(spec).__name__}")
        desired = deployment.replica_spec.target_replica_count
        deploying_revision_id = deployment.deploying_revision_id
        if deploying_revision_id is None:
            raise InvalidEndpointState(
                f"Deployment {deployment.id} has DEPLOYING lifecycle but deploying_revision_id is None. "
                "This indicates an inconsistent state — the deployment will be skipped."
            )
        classified = self._classify_routes(routes, deploying_revision_id)
        log.info(
            "deployment {}: sub_step={}, routes total={}, "
            "old_active={}, new_prov={}, new_healthy={}, new_unhealthy={}, new_failed={}",
            deployment.id,
            deployment.sub_step,
            len(routes),
            len(classified.old_active),
            classified.new_provisioning_count,
            classified.new_healthy_count,
            classified.new_unhealthy_count,
            classified.new_failed_count,
        )

        if result := self._check_completed(deployment, classified, desired):
            return result
        return self._compute_route_mutations(deployment, classified, desired, spec)

    def _classify_routes(
        self,
        routes: Sequence[RouteInfo],
        deploying_revision_id: UUID,
    ) -> _ClassifiedRoutes:
        """Classify routes into old/new by revision and status."""
        classified = _ClassifiedRoutes()
        for route in routes:
            if route.revision_id != deploying_revision_id:
                if route.status.is_active():
                    classified.old_active.append(route)
                continue

            if route.status.is_provisioning():
                classified.new_provisioning_count += 1
            elif route.status.is_inactive():
                classified.new_failed_count += 1
            elif route.status == RouteStatus.HEALTHY:
                classified.new_healthy_count += 1
            elif route.status == RouteStatus.UNHEALTHY:
                classified.new_unhealthy_count += 1
        return classified

    def _check_completed(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
    ) -> StrategyCycleResult | None:
        """Return COMPLETED result if all old routes are replaced and enough new are healthy."""
        if (
            classified.old_active
            or classified.new_provisioning_count
            or classified.new_healthy_count < desired
        ):
            return None
        log.info(
            "deployment {}: rolling update complete ({} healthy routes)",
            deployment.id,
            classified.new_healthy_count,
        )
        return StrategyCycleResult(sub_step=DeploymentLifecycleSubStep.DEPLOYING_COMPLETED)

    def _compute_route_mutations(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
        spec: RollingUpdateSpec,
    ) -> StrategyCycleResult:
        """Compute surge/unavailable budget and return PROVISIONING with route mutations.

        If new routes are still being provisioned, waits without creating or
        terminating additional routes.
        """
        if classified.new_provisioning_count:
            log.debug(
                "deployment {}: {} new routes still provisioning",
                deployment.id,
                classified.new_provisioning_count,
            )
            return StrategyCycleResult(sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING)

        max_surge = spec.max_surge  # extra routes allowed above desired
        max_unavailable = spec.max_unavailable  # routes allowed to be down

        max_total = desired + max_surge  # upper bound on simultaneous routes
        current_total = (
            len(classified.old_active) + classified.total_new_running
        )  # routes running now
        min_available = max(0, desired - max_unavailable)  # floor for traffic-serving routes

        route_changes = RouteChanges()

        to_create = self._compute_routes_to_create(desired, max_total, current_total, classified)
        if to_create > 0:
            route_changes.rollout_specs = _build_route_creators(deployment, to_create)

        to_terminate = self._compute_routes_to_terminate(classified, min_available)
        if to_terminate > 0:
            sorted_old = sorted(
                classified.old_active, key=lambda route: route.status.termination_priority()
            )
            for route in sorted_old[:to_terminate]:
                route_changes.drain_route_ids.append(route.route_id)

        log.debug(
            "deployment {}: PROVISIONING create={}, terminate={}, "
            "old_active={}, new_healthy={}, new_unhealthy={}, new_prov={}",
            deployment.id,
            to_create,
            to_terminate,
            len(classified.old_active),
            classified.new_healthy_count,
            classified.new_unhealthy_count,
            classified.new_provisioning_count,
        )

        return StrategyCycleResult(
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            route_changes=route_changes,
        )

    def _compute_routes_to_create(
        self,
        desired: int,
        max_total: int,
        current_total: int,
        classified: _ClassifiedRoutes,
    ) -> int:
        """Decide how many new routes to create within surge budget.

        Takes the smaller of two constraints:
        - ``can_create``:  surge headroom (max_total - current_total)
        - ``still_needed``: new routes remaining to reach desired

        Example (desired=4, max_surge=1 → max_total=5):
          old=4, new_running=0 → can_create=1, still_needed=4 → 1 (surge-limited)
          old=0, new_running=3 → can_create=2, still_needed=1 → 1 (goal-limited)
        """
        can_create = max_total - current_total
        still_needed = desired - classified.total_new_running
        return max(0, min(can_create, still_needed))

    def _compute_routes_to_terminate(
        self,
        classified: _ClassifiedRoutes,
        min_available: int,
    ) -> int:
        """Decide how many old routes to terminate within unavailability budget.

        Only counts truly healthy routes as available (not UNHEALTHY/DEGRADED).
        Takes the smaller of two constraints:
        - ``can_terminate``: availability headroom (available_count - min_available)
        - ``old_active``:    cannot terminate more old routes than exist

        Example (desired=4, max_unavailable=1 → min_available=3):
          new_healthy=2, old=3 → can_terminate=2, old=3 → 2 (budget-limited)
          new_healthy=4, old=1 → can_terminate=2, old=1 → 1 (old-count-limited)
        """
        available_count = classified.new_healthy_count + len(classified.old_active)
        can_terminate = available_count - min_available
        return max(0, min(can_terminate, len(classified.old_active)))  # clamp to actual old count


def _build_route_creators(
    deployment: DeploymentInfo,
    count: int,
) -> list[RBACEntityCreator[RoutingRow]]:
    """Build route creator specs for new revision routes."""
    creators: list[RBACEntityCreator[RoutingRow]] = []
    for _ in range(count):
        spec = RouteCreatorSpec(
            endpoint_id=deployment.id,
            session_owner_id=deployment.metadata.session_owner,
            domain=deployment.metadata.domain,
            project_id=deployment.metadata.project,
            revision_id=deployment.deploying_revision_id,
        )
        creators.append(
            RBACEntityCreator(
                spec=spec,
                element_type=RBACElementType.ROUTING,
                scope_ref=RBACElementRef(
                    element_type=RBACElementType.MODEL_DEPLOYMENT,
                    element_id=str(deployment.id),
                ),
            )
        )
    return creators
