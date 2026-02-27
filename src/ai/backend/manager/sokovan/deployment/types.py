from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentSubStatus,
    RouteStatus,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator

if TYPE_CHECKING:
    from ai.backend.manager.data.deployment.types import DeploymentInfoWithRoutes, RouteInfo


class DeploymentLifecycleType(StrEnum):
    CHECK_PENDING = "check_pending"
    CHECK_REPLICA = "check_replica"
    SCALING = "scaling"
    DEPLOYING = "deploying"
    RECONCILE = "reconcile"
    DESTROYING = "destroying"


class DeploymentSubStep(DeploymentSubStatus):
    """Sub-step variants shared by all deployment strategies (BEP-1049).

    Both Blue-Green and Rolling Update cycle FSMs directly return
    one of these variants. No strategy-specific statuses exist.
    """

    PROVISIONING = "provisioning"
    PROGRESSING = "progressing"
    ROLLED_BACK = "rolled_back"


@dataclass
class CycleEvaluationResult:
    """Result of evaluating one cycle of a deployment strategy.

    Returned by strategy evaluation functions (rolling_update_evaluate,
    blue_green_evaluate). Bundles the sub-step with any route changes
    that should be applied.

    When ``completed`` is True the strategy has finished and the coordinator
    should transition the deployment to READY after the handler performs
    the revision swap in its post_process.
    """

    sub_step: DeploymentSubStep
    completed: bool = False
    scale_out: list[Creator[RoutingRow]] = field(default_factory=list)
    scale_in_route_ids: list[UUID] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Result of strategy evaluation grouping deployments by sub-step.

    Attributes:
        groups: Deployments grouped by in-progress sub-step for handler dispatch.
        completed: Deployments whose strategy completed. The coordinator passes
            these to the PROGRESSING handler's post_process for revision swap,
            then transitions them to READY.
        skipped: Deployments skipped (no policy / unsupported strategy).
        errors: Deployments that failed evaluation.
    """

    groups: dict[DeploymentSubStep, list[DeploymentInfo]]
    completed: list[DeploymentInfo] = field(default_factory=list)
    skipped: list[DeploymentInfo] = field(default_factory=list)
    errors: list[DeploymentExecutionError] = field(default_factory=list)


@dataclass
class DeploymentExecutionError:
    deployment_info: DeploymentInfo
    reason: str
    error_detail: str
    error_code: str | None = None


@dataclass
class DeploymentExecutionResult:
    """Result of a deployment execution operation."""

    successes: list[DeploymentInfo] = field(default_factory=list)
    errors: list[DeploymentExecutionError] = field(default_factory=list)
    skipped: list[DeploymentInfo] = field(default_factory=list)
    completed: list[DeploymentInfo] = field(default_factory=list)


@dataclass
class AutoScalingDecision:
    """Decision made by autoscaling evaluation."""

    should_scale: bool
    new_replica_count: int | None = None
    triggered_rule_id: UUID | None = None
    scaling_direction: str | None = None  # "up" or "down"
    reason: str | None = None


@dataclass
class RouteCreationSpec:
    """Specification for creating a new route and session."""

    endpoint_id: UUID
    endpoint_name: str
    traffic_ratio: float
    image_id: UUID
    resource_group: str
    domain: str
    project: UUID
    created_user: UUID
    session_owner: UUID
    model_mount_destination: str

    # Extension methods for DeploymentInfo compatibility
    @staticmethod
    def get_target_replicas_from_deployment(deployment_info: DeploymentInfo) -> int:
        """Get the target number of replicas for a DeploymentInfo."""
        # DeploymentInfo has replica_spec.replica_count
        return deployment_info.replica_spec.replica_count

    # Extension methods for DeploymentInfoWithRoutes compatibility
    @staticmethod
    def get_healthy_route_count_from_deployment(
        deployment_with_routes: DeploymentInfoWithRoutes,
    ) -> int:
        """Get the count of healthy routes."""
        return sum(
            1
            for route in deployment_with_routes.routes
            if route.status in {RouteStatus.HEALTHY, RouteStatus.PROVISIONING}
        )

    @staticmethod
    def get_routes_to_remove_from_deployment(
        deployment_with_routes: DeploymentInfoWithRoutes, target_count: int
    ) -> list[RouteInfo]:
        """Get routes that should be removed to reach target count."""
        healthy_routes = [
            r
            for r in deployment_with_routes.routes
            if r.status in {RouteStatus.HEALTHY, RouteStatus.PROVISIONING}
        ]
        current_count = len(healthy_routes)
        if current_count <= target_count:
            return []
        # Remove routes with lowest traffic ratio first
        sorted_routes = sorted(healthy_routes, key=lambda r: r.traffic_ratio)
        return sorted_routes[: current_count - target_count]
