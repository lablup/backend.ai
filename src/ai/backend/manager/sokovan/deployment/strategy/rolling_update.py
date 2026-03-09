"""Rolling update strategy evaluation for a single deployment cycle (BEP-1049).

Classifies routes by revision (old/new) and status, then decides the next
sub-step and route mutations based on ``max_surge`` / ``max_unavailable``.
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
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec

from .types import AbstractDeploymentStrategy, RouteChanges, StrategyCycleResult

log = BraceStyleAdapter(logging.getLogger(__name__))



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
            4. If all new routes failed -> ROLLED_BACK.
            5. Compute allowed surge/unavailable, decide create/terminate -> PROGRESSING.
        """
        deploying_rev = deployment.deploying_revision_id
        desired = deployment.replica_spec.target_replica_count

        # -- 1. Classify routes --
        old_active: list[RouteInfo] = []
        new_provisioning: list[RouteInfo] = []
        new_healthy: list[RouteInfo] = []
        new_failed: list[RouteInfo] = []

        for r in routes:
            is_new = r.revision_id == deploying_rev
            if not is_new:
                if r.status.is_active():
                    old_active.append(r)
                continue

            if r.status == RouteStatus.PROVISIONING:
                new_provisioning.append(r)
            elif r.status == RouteStatus.HEALTHY:
                new_healthy.append(r)
            elif r.status in (RouteStatus.FAILED_TO_START, RouteStatus.TERMINATED):
                new_failed.append(r)
            elif r.status.is_active():
                new_healthy.append(r)

        total_new_live = len(new_provisioning) + len(new_healthy)

        # -- 2. PROVISIONING: wait for in-flight routes --
        if new_provisioning:
            log.debug(
                "deployment {}: {} new routes still provisioning",
                deployment.id,
                len(new_provisioning),
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.PROVISIONING)

        # -- 3. Completed: all old replaced, enough new healthy --
        if not old_active and len(new_healthy) >= desired:
            log.info(
                "deployment {}: rolling update complete ({} healthy routes)",
                deployment.id,
                len(new_healthy),
            )
            return StrategyCycleResult(
                sub_step=DeploymentSubStep.COMPLETED,
            )

        # -- 4. Rolled back: every new route failed --
        if total_new_live == 0 and new_failed:
            log.warning(
                "deployment {}: all {} new routes failed — rolling back",
                deployment.id,
                len(new_failed),
            )
            return StrategyCycleResult(sub_step=DeploymentSubStep.ROLLED_BACK)

        # -- 5. PROGRESSING: compute surge / unavailable budget --
        spec = self._spec
        max_surge = spec.max_surge
        max_unavailable = spec.max_unavailable

        # Total pods allowed at peak = desired + max_surge
        max_total = desired + max_surge
        current_total = len(old_active) + total_new_live

        # Minimum available pods = desired - max_unavailable
        min_available = max(0, desired - max_unavailable)

        route_changes = RouteChanges()

        # Decide how many new routes to create
        can_create = max_total - current_total
        still_needed = desired - total_new_live
        to_create = max(0, min(can_create, still_needed))

        if to_create > 0:
            route_changes.rollout_specs = _build_route_creators(deployment, to_create)

        # Decide how many old routes to terminate
        available_count = len(new_healthy) + len(old_active)
        can_terminate = available_count - min_available
        to_terminate = max(0, min(can_terminate, len(old_active)))

        if to_terminate > 0:
            # Terminate old routes with lowest termination priority first
            sorted_old = sorted(old_active, key=lambda r: r.status.termination_priority())
            for r in sorted_old[:to_terminate]:
                route_changes.drain_route_ids.append(r.route_id)

        log.debug(
            "deployment {}: PROGRESSING create={}, terminate={}, "
            "old_active={}, new_healthy={}, new_prov={}",
            deployment.id,
            to_create,
            to_terminate,
            len(old_active),
            len(new_healthy),
            len(new_provisioning),
        )

        return StrategyCycleResult(
            sub_step=DeploymentSubStep.PROGRESSING,
            route_changes=route_changes,
        )


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
