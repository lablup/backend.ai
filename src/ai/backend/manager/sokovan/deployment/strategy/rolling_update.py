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

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentSubStep,
    RouteInfo,
    RouteStatus,
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.exceptions import InvalidEndpointState

from .types import AbstractDeploymentStrategy, RouteChanges, StrategyCycleResult

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class _ClassifiedRoutes:
    """Routes classified by revision and status."""

    old_active: list[RouteInfo] = field(default_factory=list)
    new_provisioning: list[RouteInfo] = field(default_factory=list)
    new_healthy: list[RouteInfo] = field(default_factory=list)
    new_unhealthy: list[RouteInfo] = field(default_factory=list)
    new_failed: list[RouteInfo] = field(default_factory=list)

    @property
    def total_new_live(self) -> int:
        return len(self.new_provisioning) + len(self.new_healthy) + len(self.new_unhealthy)


class RollingUpdateStrategy(AbstractDeploymentStrategy):
    """Rolling update deployment strategy FSM."""

    _spec: RollingUpdateSpec

    def __init__(self, spec: RollingUpdateSpec) -> None:
        super().__init__(spec)
        self._spec = spec

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
    ) -> StrategyCycleResult:
        """Evaluate one cycle of rolling update for a single deployment.

        FSM flow:
            1. Classify routes into old / new by revision_id.
            2. If any new route is PROVISIONING -> PROVISIONING (wait).
            3. If no old routes remain and new_healthy >= desired -> COMPLETED.
            4. If all new routes failed or is unhealthy -> ROLLED_BACK.
            5. Compute allowed surge/unavailable, decide create/terminate -> PROGRESSING.
        """
        desired = deployment.replica_spec.target_replica_count
        deploying_revision_id = deployment.deploying_revision_id
        if deploying_revision_id is None:
            raise InvalidEndpointState(
                f"Deployment {deployment.id} has DEPLOYING lifecycle but deploying_revision_id is None. "
                "This indicates an inconsistent state — the deployment will be skipped."
            )
        classified = self._classify_routes(routes, deploying_revision_id)

        if result := self._check_provisioning(deployment, classified):
            return result
        if result := self._check_completed(deployment, classified, desired):
            return result
        if result := self._check_rolled_back(deployment, classified):
            return result
        return self._compute_progressing(deployment, classified, desired)

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

            if route.status in (RouteStatus.PROVISIONING, RouteStatus.DEGRADED):
                # DEGRADED routes are still warming up (health checks not yet
                # passing) — treat them like PROVISIONING so they are not
                # mistakenly counted as unhealthy and trigger a premature rollback.
                classified.new_provisioning.append(route)
            elif route.status == RouteStatus.HEALTHY:
                classified.new_healthy.append(route)
            elif route.status == RouteStatus.UNHEALTHY:
                classified.new_unhealthy.append(route)
            elif route.status in (RouteStatus.FAILED_TO_START, RouteStatus.TERMINATED):
                classified.new_failed.append(route)
        return classified

    def _check_provisioning(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
    ) -> StrategyCycleResult | None:
        """Return PROVISIONING result if any new routes are still being provisioned."""
        if not classified.new_provisioning:
            return None
        log.debug(
            "deployment {}: {} new routes still provisioning",
            deployment.id,
            len(classified.new_provisioning),
        )
        return StrategyCycleResult(sub_step=DeploymentSubStep.PROVISIONING)

    def _check_completed(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
    ) -> StrategyCycleResult | None:
        """Return COMPLETED result if all old routes are replaced and enough new are healthy."""
        if classified.old_active or len(classified.new_healthy) < desired:
            return None
        log.info(
            "deployment {}: rolling update complete ({} healthy routes)",
            deployment.id,
            len(classified.new_healthy),
        )
        return StrategyCycleResult(sub_step=DeploymentSubStep.COMPLETED)

    def _check_rolled_back(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
    ) -> StrategyCycleResult | None:
        """Return ROLLED_BACK result if all new routes have failed or are unhealthy."""
        if classified.total_new_live == 0 and classified.new_failed:
            log.warning(
                "deployment {}: all {} new routes failed — rolling back",
                deployment.id,
                len(classified.new_failed),
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.ROLLED_BACK)

        if (
            not classified.new_healthy
            and not classified.new_provisioning
            and classified.new_unhealthy
        ):
            log.warning(
                "deployment {}: all {} new routes unhealthy — rolling back",
                deployment.id,
                len(classified.new_unhealthy),
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.ROLLED_BACK)

        return None

    def _compute_progressing(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
    ) -> StrategyCycleResult:
        """Compute surge/unavailable budget and return PROGRESSING with route mutations."""
        max_surge = self._spec.max_surge
        max_unavailable = self._spec.max_unavailable

        max_total = desired + max_surge
        current_total = len(classified.old_active) + classified.total_new_live
        min_available = max(0, desired - max_unavailable)

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
            "deployment {}: PROGRESSING create={}, terminate={}, "
            "old_active={}, new_healthy={}, new_unhealthy={}, new_prov={}",
            deployment.id,
            to_create,
            to_terminate,
            len(classified.old_active),
            len(classified.new_healthy),
            len(classified.new_unhealthy),
            len(classified.new_provisioning),
        )

        return StrategyCycleResult(
            sub_step=DeploymentSubStep.PROGRESSING,
            route_changes=route_changes,
        )

    def _compute_routes_to_create(
        self,
        desired: int,
        max_total: int,
        current_total: int,
        classified: _ClassifiedRoutes,
    ) -> int:
        """Decide how many new routes to create within surge budget."""
        can_create = max_total - current_total
        still_needed = desired - classified.total_new_live
        return max(0, min(can_create, still_needed))

    def _compute_routes_to_terminate(
        self,
        classified: _ClassifiedRoutes,
        min_available: int,
    ) -> int:
        """Decide how many old routes to terminate within unavailability budget.

        Only counts truly healthy routes as available (not UNHEALTHY/DEGRADED).
        Includes a safety guard: when ``min_available > 0`` and no new routes are
        healthy yet, at least one old route is preserved to avoid a complete
        traffic outage.
        """
        available_count = len(classified.new_healthy) + len(classified.old_active)
        can_terminate = available_count - min_available
        to_terminate = max(0, min(can_terminate, len(classified.old_active)))

        # Safety guard: when max_unavailable < desired the operator expects at
        # least *some* routes to stay available.  Never terminate ALL old routes
        # in that case until at least one new route is healthy — otherwise the
        # deployment suffers a complete traffic outage.
        # When max_unavailable >= desired (min_available == 0), the operator has
        # explicitly opted into full unavailability, so we honour that.
        if (
            min_available > 0
            and len(classified.new_healthy) == 0
            and to_terminate >= len(classified.old_active)
            and len(classified.old_active) > 0
        ):
            to_terminate = len(classified.old_active) - 1

        return to_terminate


def _build_route_creators(
    deployment: DeploymentInfo,
    count: int,
) -> list[Creator[RoutingRow]]:
    """Build route creator specs for new revision routes."""
    creators: list[Creator[RoutingRow]] = []
    for _ in range(count):
        spec = RouteCreatorSpec(
            endpoint_id=deployment.id,
            session_owner_id=deployment.metadata.session_owner,
            domain=deployment.metadata.domain,
            project_id=deployment.metadata.project,
            revision_id=deployment.deploying_revision_id,
        )
        creators.append(Creator(spec=spec))
    return creators
