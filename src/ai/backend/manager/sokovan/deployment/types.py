from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional
from uuid import UUID

from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import RouteStatus


class DeploymentLifecycleType(StrEnum):
    CHECK_PENDING = "check_pending"
    CHECK_REPLICA = "check_replica"
    SCALING = "scaling"
    RECONCILE = "reconcile"
    DESTROYING = "destroying"


@dataclass
class DeploymentExecutionError:
    deployment_info: DeploymentInfo
    reason: str
    error_detail: str


@dataclass
class DeploymentExecutionResult:
    """Result of a deployment execution operation."""

    successes: list[DeploymentInfo] = field(default_factory=list)
    errors: list[DeploymentExecutionError] = field(default_factory=list)
    skipped: list[DeploymentInfo] = field(default_factory=list)


@dataclass
class AutoScalingDecision:
    """Decision made by autoscaling evaluation."""

    should_scale: bool
    new_replica_count: Optional[int] = None
    triggered_rule_id: Optional[UUID] = None
    scaling_direction: Optional[str] = None  # "up" or "down"
    reason: Optional[str] = None


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
    def get_target_replicas_from_deployment(deployment_info) -> int:
        """Get the target number of replicas for a DeploymentInfo."""
        # DeploymentInfo has replica_spec.replica_count
        return deployment_info.replica_spec.replica_count

    # Extension methods for DeploymentInfoWithRoutes compatibility
    @staticmethod
    def get_healthy_route_count_from_deployment(deployment_with_routes) -> int:
        """Get the count of healthy routes."""
        return sum(
            1
            for route in deployment_with_routes.routes
            if route.status in {RouteStatus.HEALTHY, RouteStatus.PROVISIONING}
        )

    @staticmethod
    def get_routes_to_remove_from_deployment(deployment_with_routes, target_count: int):
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
