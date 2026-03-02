"""Blue-green deployment strategy evaluation for a single deployment cycle (BEP-1049).

Provisions a full set of new-revision routes (INACTIVE), validates them, then
atomically switches traffic from the old revision to the new one.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentSubStep,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.deployment_policy import BlueGreenSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec

from .types import AbstractDeploymentStrategy, RouteChanges, StrategyCycleResult

log = BraceStyleAdapter(logging.getLogger(__name__))


class BlueGreenStrategy(AbstractDeploymentStrategy):
    """Blue-green deployment strategy FSM."""

    def __init__(self, spec: BlueGreenSpec) -> None:
        super().__init__(spec)
        self._spec = spec

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
    ) -> StrategyCycleResult:
        """Evaluate one cycle of blue-green deployment for a single deployment.

        FSM flow:
            1. Classify routes into blue (old) / green (new) by revision_id.
            2. If no green routes → create all green (INACTIVE) → PROVISIONING.
            3. If any green PROVISIONING → PROVISIONING (wait).
            4. If all green failed → drain green → ROLLED_BACK.
            5. If not all green healthy → PROGRESSING (wait).
            6. If all green healthy + auto_promote=False → PROGRESSING (manual wait).
            7. If all green healthy + auto_promote=True + delay>0 → PROGRESSING (delay wait).
            8. If all green healthy + auto_promote=True + delay=0 → promote + COMPLETED.
        """
        deploying_rev = deployment.deploying_revision_id
        desired = deployment.replica_spec.target_replica_count

        # ── 1. Classify routes ──
        blue_active: list[RouteInfo] = []
        green_provisioning: list[RouteInfo] = []
        green_healthy: list[RouteInfo] = []
        green_failed: list[RouteInfo] = []

        for r in routes:
            is_green = r.revision_id == deploying_rev
            if not is_green:
                if r.status.is_active():
                    blue_active.append(r)
                continue

            if r.status == RouteStatus.PROVISIONING:
                green_provisioning.append(r)
            elif r.status == RouteStatus.HEALTHY:
                green_healthy.append(r)
            elif r.status in (RouteStatus.FAILED_TO_START, RouteStatus.TERMINATED):
                green_failed.append(r)
            elif r.status.is_active():
                green_healthy.append(r)

        total_green_live = len(green_provisioning) + len(green_healthy)

        # ── 2. No green routes → create all green (INACTIVE) ──
        if total_green_live == 0 and not green_failed:
            log.debug(
                "deployment {}: no green routes — creating {} INACTIVE routes",
                deployment.id,
                desired,
            )
            route_changes = RouteChanges(
                rollout_specs=_build_route_creators(deployment, desired),
            )
            return StrategyCycleResult(
                sub_step=DeploymentSubStep.PROVISIONING,
                route_changes=route_changes,
            )

        # ── 3. Green PROVISIONING → wait ──
        if green_provisioning:
            log.debug(
                "deployment {}: {} green routes still provisioning",
                deployment.id,
                len(green_provisioning),
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.PROVISIONING)

        # ── 4. All green failed → rollback ──
        if total_green_live == 0 and green_failed:
            log.warning(
                "deployment {}: all {} green routes failed — rolling back",
                deployment.id,
                len(green_failed),
            )
            route_changes = RouteChanges(
                drain_route_ids=[r.route_id for r in green_failed],
            )
            return StrategyCycleResult(
                sub_step=DeploymentSubStep.ROLLED_BACK,
                route_changes=route_changes,
            )

        # ── 5. Not all green healthy → PROGRESSING (wait) ──
        if len(green_healthy) < desired:
            log.debug(
                "deployment {}: green healthy={}/{} — waiting",
                deployment.id,
                len(green_healthy),
                desired,
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.PROGRESSING)

        # ── All green healthy from here ──

        # ── 6. auto_promote=False → PROGRESSING (manual wait) ──
        if not self._spec.auto_promote:
            log.debug(
                "deployment {}: all green healthy, waiting for manual promotion",
                deployment.id,
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.PROGRESSING)

        # ── 7. auto_promote=True + delay>0 → PROGRESSING (delay wait) ──
        if self._spec.promote_delay_seconds > 0:
            log.debug(
                "deployment {}: all green healthy, waiting for promote delay ({}s)",
                deployment.id,
                self._spec.promote_delay_seconds,
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.PROGRESSING)

        # ── 8. Promotion: green → ACTIVE, blue → TERMINATING ──
        log.info(
            "deployment {}: promoting {} green routes, terminating {} blue routes",
            deployment.id,
            len(green_healthy),
            len(blue_active),
        )
        route_changes = RouteChanges(
            promote_route_ids=[r.route_id for r in green_healthy],
            drain_route_ids=[r.route_id for r in blue_active],
        )
        return StrategyCycleResult(
            sub_step=DeploymentSubStep.COMPLETED,
            route_changes=route_changes,
        )


def _build_route_creators(
    deployment: DeploymentInfo,
    count: int,
) -> list[Creator[RoutingRow]]:
    """Build route creator specs for green routes (INACTIVE, traffic_ratio=0.0)."""
    creators: list[Creator[RoutingRow]] = []
    for _ in range(count):
        creator_spec = RouteCreatorSpec(
            endpoint_id=deployment.id,
            session_owner_id=deployment.metadata.session_owner,
            domain=deployment.metadata.domain,
            project_id=deployment.metadata.project,
            revision_id=deployment.deploying_revision_id,
            traffic_status=RouteTrafficStatus.INACTIVE,
            traffic_ratio=0.0,
        )
        creators.append(Creator(spec=creator_spec))
    return creators
