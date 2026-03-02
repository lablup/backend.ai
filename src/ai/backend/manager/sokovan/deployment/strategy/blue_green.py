"""Blue-green deployment strategy evaluation for a single deployment cycle (BEP-1049).

Provisions a full set of new-revision routes, validates them, then atomically
switches traffic from the old revision to the new one.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

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

from .types import CycleEvaluationResult, RouteChanges


def blue_green_evaluate(
    deployment: DeploymentInfo,
    routes: Sequence[RouteInfo],
    spec: BlueGreenSpec,
) -> CycleEvaluationResult:
    """Evaluate one cycle of blue-green deployment for a single deployment.

    FSM Steps:
        1. Classify routes into blue (old revision) and green (new/deploying revision).
        2. If no green routes exist, create ``desired`` green routes (INACTIVE).
        3. If any green is PROVISIONING, wait.
        4. If all green routes FAILED, rollback.
        5. If healthy green < desired, wait.
        6. All green healthy + auto_promote=False → wait for manual promotion.
        7. All green healthy + auto_promote=True + delay not elapsed → wait.
        8. All green healthy + auto_promote=True + delay elapsed → promote.
    """
    deploying_revision = deployment.deploying_revision_id
    desired = deployment.replica_spec.target_replica_count

    # ── Step 1: Classify routes ──
    green: list[RouteInfo] = []
    blue: list[RouteInfo] = []
    for r in routes:
        if r.revision_id is not None and r.revision_id == deploying_revision:
            green.append(r)
        else:
            blue.append(r)

    green_provisioning = [r for r in green if r.status == RouteStatus.PROVISIONING]
    green_healthy = [r for r in green if r.status == RouteStatus.HEALTHY]
    green_failed = [
        r for r in green if r.status in (RouteStatus.FAILED_TO_START, RouteStatus.TERMINATED)
    ]
    blue_active = [r for r in blue if r.status.is_active()]

    # ── Step 2: No green routes → create them (INACTIVE, ratio=0.0) ──
    if not green:
        creators = _build_route_creators(deployment, desired)
        return CycleEvaluationResult(
            sub_step=DeploymentSubStep.PROVISIONING,
            route_changes=RouteChanges(scale_out_specs=creators),
        )

    # ── Step 3: Green PROVISIONING exists → wait ──
    if green_provisioning:
        return CycleEvaluationResult(sub_step=DeploymentSubStep.PROVISIONING)

    # ── Step 4: All green failed → rollback ──
    if green_failed and not green_healthy:
        return CycleEvaluationResult(
            sub_step=DeploymentSubStep.ROLLED_BACK,
            route_changes=RouteChanges(
                scale_in_route_ids=[r.route_id for r in green_failed],
            ),
        )

    # ── Step 5: Healthy green < desired → wait (progressing) ──
    if len(green_healthy) < desired:
        return CycleEvaluationResult(sub_step=DeploymentSubStep.PROGRESSING)

    # ── Step 6: All green healthy + auto_promote=False → manual wait ──
    if not spec.auto_promote:
        return CycleEvaluationResult(sub_step=DeploymentSubStep.PROGRESSING)

    # ── Step 7: auto_promote=True + delay check ──
    if spec.promote_delay_seconds > 0:
        latest_healthy_at = _latest_status_updated_at(green_healthy)
        if latest_healthy_at is None:
            return CycleEvaluationResult(sub_step=DeploymentSubStep.PROGRESSING)
        elapsed = (datetime.now(UTC) - latest_healthy_at).total_seconds()
        if elapsed < spec.promote_delay_seconds:
            return CycleEvaluationResult(sub_step=DeploymentSubStep.PROGRESSING)

    # ── Step 8: Promote green, terminate blue ──
    return CycleEvaluationResult(
        sub_step=DeploymentSubStep.PROGRESSING,
        completed=True,
        route_changes=RouteChanges(
            promote_route_ids=[r.route_id for r in green_healthy],
            scale_in_route_ids=[r.route_id for r in blue_active],
        ),
    )


def _latest_status_updated_at(routes: list[RouteInfo]) -> datetime | None:
    """Return the most recent status_updated_at among the given routes."""
    timestamps = [r.status_updated_at for r in routes if r.status_updated_at is not None]
    return max(timestamps) if timestamps else None


def _build_route_creators(
    deployment: DeploymentInfo,
    count: int,
) -> list[Creator[RoutingRow]]:
    """Build route creators for green routes (INACTIVE, traffic_ratio=0.0)."""
    return [
        Creator(
            spec=RouteCreatorSpec(
                endpoint_id=deployment.id,
                session_owner_id=deployment.metadata.session_owner,
                domain=deployment.metadata.domain,
                project_id=deployment.metadata.project,
                traffic_ratio=0.0,
                revision_id=deployment.deploying_revision_id,
                traffic_status=RouteTrafficStatus.INACTIVE,
            )
        )
        for _ in range(count)
    ]
