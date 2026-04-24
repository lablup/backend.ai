"""Blue-green deployment strategy evaluation for a single deployment cycle (BEP-1049).

Provisions a full set of new-revision routes, validates them, then atomically
switches traffic from the old revision to the new one.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    RouteHealthStatus,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, DeploymentStrategySpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.exceptions import InvalidEndpointState

from .types import AbstractDeploymentStrategy, RouteChanges, StrategyCycleResult

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class _ClassifiedRoutes:
    """Routes classified by revision and status.

    Only ``blue_active`` and ``green_healthy`` retain full RouteInfo
    (needed for drain/promote route IDs and delay calculation).
    Other buckets store counts only.
    """

    blue_active: list[RouteInfo] = field(default_factory=list)
    green_healthy: list[RouteInfo] = field(default_factory=list)
    green_provisioning_count: int = 0
    green_unhealthy_count: int = 0
    green_failed_count: int = 0

    @property
    def total_green_running(self) -> int:
        """Count of green-revision routes whose processes are still running.

        Includes provisioning and unhealthy routes to prevent duplicate route
        creation.  (Unhealthy routes are excluded from promotion decisions
        since they cannot serve traffic reliably.)
        """
        return self.green_provisioning_count + len(self.green_healthy) + self.green_unhealthy_count


class BlueGreenStrategy(AbstractDeploymentStrategy):
    """Blue-green deployment strategy FSM."""

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
        spec: DeploymentStrategySpec,
    ) -> StrategyCycleResult:
        """Evaluate one cycle of blue-green deployment for a single deployment.

        FSM flow:
            1. Classify routes into blue (old) / green (new) by revision_id.
            2. If all green healthy + auto_promote + delay met → COMPLETED.
            3. If all green healthy but promotion not met → AWAITING_PROMOTION.
            4. Otherwise → PROVISIONING (create routes / wait for readiness).

        Rollback is not decided by the FSM — the coordinator's timeout
        sweep handles it by transitioning to ROLLING_BACK when the
        deploying timeout is exceeded.
        """
        if not isinstance(spec, BlueGreenSpec):
            raise TypeError(f"Expected BlueGreenSpec, got {type(spec).__name__}")
        desired = deployment.replica_spec.target_replica_count
        deploying_revision = deployment.deploying_revision_id
        if deploying_revision is None:
            raise InvalidEndpointState(
                f"Deployment {deployment.id} has DEPLOYING lifecycle but deploying_revision_id is None. "
                "This indicates an inconsistent state — the deployment will be skipped."
            )

        classified = self._classify_routes(routes, deploying_revision)

        log.debug(
            "deployment {}: sub_step={}, routes total={}, "
            "blue_active={}, green_prov={}, green_healthy={}, green_unhealthy={}, green_failed={}",
            deployment.id,
            deployment.sub_step,
            len(routes),
            len(classified.blue_active),
            classified.green_provisioning_count,
            len(classified.green_healthy),
            classified.green_unhealthy_count,
            classified.green_failed_count,
        )

        if result := self._check_awaiting_promotion(deployment, classified, desired):
            return result
        return self._compute_route_mutations(deployment, classified, desired)

    def _classify_routes(
        self,
        routes: Sequence[RouteInfo],
        deploying_revision: uuid.UUID,
    ) -> _ClassifiedRoutes:
        """Classify routes into blue (old) / green (new) buckets."""
        classified = _ClassifiedRoutes()
        for route in routes:
            is_green = route.revision_id == deploying_revision
            if not is_green:
                if route.status.is_active():
                    classified.blue_active.append(route)
                continue

            if route.status == RouteStatus.PROVISIONING:
                classified.green_provisioning_count += 1
            elif route.status.is_inactive():
                classified.green_failed_count += 1
            elif route.health_status == RouteHealthStatus.HEALTHY:
                classified.green_healthy.append(route)
            else:
                classified.green_unhealthy_count += 1
        return classified

    def _check_awaiting_promotion(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
    ) -> StrategyCycleResult | None:
        """Return AWAITING_PROMOTION when all green are healthy but promotion conditions not met."""
        if len(classified.green_healthy) < desired:
            return None
        log.debug(
            "deployment {}: all green healthy, awaiting promotion",
            deployment.id,
        )
        return StrategyCycleResult(sub_step=DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION)

    def _compute_route_mutations(
        self,
        deployment: DeploymentInfo,
        classified: _ClassifiedRoutes,
        desired: int,
    ) -> StrategyCycleResult:
        """Return PROVISIONING — create green routes or wait for readiness.

        This is the default fallback when AWAITING_PROMOTION
        conditions are not met.
        """
        # No green routes at all → create the full set as INACTIVE
        if classified.total_green_running == 0 and not classified.green_failed_count:
            log.debug(
                "deployment {}: no green routes — creating {} INACTIVE routes",
                deployment.id,
                desired,
            )
            return StrategyCycleResult(
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
                route_changes=RouteChanges(
                    rollout_specs=_build_green_route_creators(deployment, desired),
                ),
            )

        # Green routes still provisioning or not enough healthy → wait
        log.debug(
            "deployment {}: green healthy={}/{}, provisioning={} — waiting",
            deployment.id,
            len(classified.green_healthy),
            desired,
            classified.green_provisioning_count,
        )
        return StrategyCycleResult(sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING)


def _build_green_route_creators(
    deployment: DeploymentInfo,
    count: int,
) -> list[RBACEntityCreator[RoutingRow]]:
    """Build route creator specs for green routes."""
    if deployment.deploying_revision_id is None:
        raise InvalidEndpointState(
            f"Deployment {deployment.id} has no deploying_revision_id; cannot build route creators."
        )
    creators: list[RBACEntityCreator[RoutingRow]] = []
    for _ in range(count):
        spec = RouteCreatorSpec(
            endpoint_id=deployment.id,
            session_owner_id=deployment.metadata.session_owner,
            domain=deployment.metadata.domain,
            project_id=deployment.metadata.project,
            revision_id=deployment.deploying_revision_id,
            traffic_status=RouteTrafficStatus.INACTIVE,
            traffic_ratio=0.0,
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
