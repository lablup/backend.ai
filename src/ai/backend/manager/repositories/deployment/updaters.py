"""UpdaterSpec implementations for deployment repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.data.deployment.types import RouteStatus, RouteTrafficStatus
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DeploymentMetadataUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for deployment metadata updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    domain: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    project: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    tag: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.domain.update_dict(to_update, "domain")
        self.project.update_dict(to_update, "project")
        self.resource_group.update_dict(to_update, "resource_group")
        self.tag.update_dict(to_update, "tag")
        return to_update


@dataclass
class ReplicaSpecUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for replica specification updates."""

    replica_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    desired_replica_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        # Use the actual database column names
        self.replica_count.update_dict(to_update, "replicas")
        self.desired_replica_count.update_dict(to_update, "desired_replicas")
        return to_update


@dataclass
class DeploymentNetworkSpecUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for deployment network specification updates."""

    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    url: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.open_to_public.update_dict(to_update, "open_to_public")
        self.url.update_dict(to_update, "url")
        return to_update


@dataclass
class MountUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for mount-related updates."""

    model_vfolder_id: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.model_vfolder_id.update_dict(to_update, "model_vfolder_id")
        return to_update


@dataclass
class RevisionStateUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for deployment revision state updates.

    Manages which revision is currently active and which is being deployed.
    """

    current_revision: TriState[UUID] = field(default_factory=TriState[UUID].nop)
    deploying_revision: TriState[UUID] = field(default_factory=TriState[UUID].nop)
    revision_history_limit: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.current_revision.update_dict(to_update, "current_revision")
        self.deploying_revision.update_dict(to_update, "deploying_revision")
        self.revision_history_limit.update_dict(to_update, "revision_history_limit")
        return to_update


@dataclass
class DeploymentUpdaterSpec(UpdaterSpec[EndpointRow]):
    """Composite UpdaterSpec for deployment updates.

    Combines metadata, replica_spec, network, mount, and revision_state updates.
    """

    metadata: Optional[DeploymentMetadataUpdaterSpec] = None
    replica_spec: Optional[ReplicaSpecUpdaterSpec] = None
    network: Optional[DeploymentNetworkSpecUpdaterSpec] = None
    mount: Optional[MountUpdaterSpec] = None
    revision_state: Optional[RevisionStateUpdaterSpec] = None

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        if self.metadata:
            to_update.update(self.metadata.build_values())
        if self.replica_spec:
            to_update.update(self.replica_spec.build_values())
        if self.network:
            to_update.update(self.network.build_values())
        if self.mount:
            to_update.update(self.mount.build_values())
        if self.revision_state:
            to_update.update(self.revision_state.build_values())
        return to_update


@dataclass
class DeploymentAutoScalingPolicyUpdaterSpec(UpdaterSpec[DeploymentAutoScalingPolicyRow]):
    """UpdaterSpec for deployment auto-scaling policy updates.

    All fields are optional - only specified fields will be updated.
    Supports partial updates for hysteresis-based scaling configuration.
    """

    min_replicas: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_replicas: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    metric_source: TriState[AutoScalingMetricSource] = field(
        default_factory=TriState[AutoScalingMetricSource].nop
    )
    metric_name: TriState[str] = field(default_factory=TriState[str].nop)
    comparator: TriState[AutoScalingMetricComparator] = field(
        default_factory=TriState[AutoScalingMetricComparator].nop
    )
    scale_up_threshold: TriState[Decimal] = field(default_factory=TriState[Decimal].nop)
    scale_down_threshold: TriState[Decimal] = field(default_factory=TriState[Decimal].nop)
    scale_up_step_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    scale_down_step_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    cooldown_seconds: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[DeploymentAutoScalingPolicyRow]:
        return DeploymentAutoScalingPolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.min_replicas.update_dict(to_update, "min_replicas")
        self.max_replicas.update_dict(to_update, "max_replicas")
        self.metric_source.update_dict(to_update, "metric_source")
        self.metric_name.update_dict(to_update, "metric_name")
        self.comparator.update_dict(to_update, "comparator")
        self.scale_up_threshold.update_dict(to_update, "scale_up_threshold")
        self.scale_down_threshold.update_dict(to_update, "scale_down_threshold")
        self.scale_up_step_size.update_dict(to_update, "scale_up_step_size")
        self.scale_down_step_size.update_dict(to_update, "scale_down_step_size")
        self.cooldown_seconds.update_dict(to_update, "cooldown_seconds")
        return to_update


@dataclass
class DeploymentPolicyUpdaterSpec(UpdaterSpec[DeploymentPolicyRow]):
    """UpdaterSpec for deployment policy updates.

    All fields are optional - only specified fields will be updated.
    Supports partial updates for deployment strategy configuration.
    """

    strategy: OptionalState[DeploymentStrategy] = field(
        default_factory=OptionalState[DeploymentStrategy].nop
    )
    strategy_spec: OptionalState[RollingUpdateSpec | BlueGreenSpec] = field(
        default_factory=OptionalState[RollingUpdateSpec | BlueGreenSpec].nop
    )
    rollback_on_failure: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[DeploymentPolicyRow]:
        return DeploymentPolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.strategy.update_dict(to_update, "strategy")
        # Convert Pydantic model to dict for JSONB storage
        spec_value = self.strategy_spec.optional_value()
        if spec_value is not None:
            to_update["strategy_spec"] = spec_value.model_dump()
        self.rollback_on_failure.update_dict(to_update, "rollback_on_failure")
        return to_update


@dataclass
class RouteStatusUpdaterSpec(UpdaterSpec[RoutingRow]):
    """UpdaterSpec for route status updates.

    Updates health status and traffic status of a route.
    """

    status: OptionalState[RouteStatus] = field(default_factory=OptionalState[RouteStatus].nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(
        default_factory=OptionalState[RouteTrafficStatus].nop
    )

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.status.update_dict(to_update, "status")
        self.traffic_status.update_dict(to_update, "traffic_status")
        return to_update


@dataclass
class RouteSessionUpdaterSpec(UpdaterSpec[RoutingRow]):
    """UpdaterSpec for route session binding.

    Binds a session to a route for traffic routing.
    """

    session: UUID

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "status": RouteStatus.PROVISIONING,
        }


@dataclass
class RouteUpdaterSpec(UpdaterSpec[RoutingRow]):
    """Unified UpdaterSpec for route updates.

    Combines all route update operations into a single spec.
    Each field uses OptionalState to support partial updates.
    """

    status: OptionalState[RouteStatus] = field(default_factory=OptionalState[RouteStatus].nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(
        default_factory=OptionalState[RouteTrafficStatus].nop
    )
    session: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    traffic_ratio: OptionalState[float] = field(default_factory=OptionalState[float].nop)
    revision: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    error_data: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.status.update_dict(to_update, "status")
        self.traffic_status.update_dict(to_update, "traffic_status")
        self.session.update_dict(to_update, "session")
        self.traffic_ratio.update_dict(to_update, "traffic_ratio")
        self.revision.update_dict(to_update, "revision")
        self.error_data.update_dict(to_update, "error_data")
        return to_update
