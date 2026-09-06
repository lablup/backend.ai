"""Update specs for the endpoint tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.endpoint.types import ScalingState
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    ClusterMode,
    ResourceSlot,
    RuleId,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
)
from ai.backend.manager.data.model_serving.modifier import ExtraMount, ImageRef
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
    EndpointLifecycle,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint.conditions import DeploymentConditions
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow, EndpointRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DeploymentUpdater(DataUpdater[EndpointRow, DeploymentInfo]):
    """Edits a deployment's own columns: metadata, replica count, network."""

    deployment_id: DeploymentID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    domain: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    project: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    tag: TriState[str] = field(default_factory=TriState[str].nop)
    replica_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    url: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.deployment_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.domain.update_dict(to_update, "domain")
        self.project.update_dict(to_update, "project")
        self.resource_group.update_dict(to_update, "resource_group")
        self.tag.update_dict(to_update, "tag")
        # The scaling goal is COALESCE(desired_replicas, replicas), so a manual
        # scale must write desired_replicas too; a stale one would override it.
        self.replica_count.update_dict(to_update, "replicas")
        self.replica_count.update_dict(to_update, "desired_replicas")
        self.open_to_public.update_dict(to_update, "open_to_public")
        self.url.update_dict(to_update, "url")
        return to_update

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()


@dataclass
class EndpointReplicaGroupUpdater(DataUpdater[EndpointRow, DeploymentInfo]):
    """Writes the replica-group pointers: the rollout target group (PROVISIONING sets
    it, PROMOTING clears it) and the serving primary (PROMOTING swaps it)."""

    deployment_id: DeploymentID
    primary_replica_group_id: OptionalState[ReplicaGroupID] = field(
        default_factory=OptionalState[ReplicaGroupID].nop
    )
    target_replica_group_id: TriState[ReplicaGroupID] = field(
        default_factory=TriState[ReplicaGroupID].nop
    )

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.deployment_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.primary_replica_group_id.update_dict(to_update, "primary_replica_group_id")
        self.target_replica_group_id.update_dict(to_update, "target_replica_group_id")
        return to_update

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()


@dataclass
class LegacyEndpointUpdater(DataUpdater[EndpointRow, DeploymentInfo]):
    """The legacy (GraphQL) endpoint edit.

    Revision-level fields are carried but not written here: a change to any of
    them creates a new revision instead, which is what ``has_revision_changes``
    is read for.
    """

    deployment_id: DeploymentID
    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    resource_opts: TriState[dict[str, Any]] = field(default_factory=TriState[dict[str, Any]].nop)
    cluster_mode: OptionalState[ClusterMode] = field(default_factory=OptionalState[ClusterMode].nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    replicas: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    image: TriState[ImageRef] = field(default_factory=TriState.nop)
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    model_definition_path: TriState[str] = field(default_factory=TriState[str].nop)
    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    extra_mounts: OptionalState[list[ExtraMount]] = field(
        default_factory=OptionalState[list[ExtraMount]].nop
    )
    environ: TriState[dict[str, str]] = field(default_factory=TriState[dict[str, str]].nop)
    runtime_variant_id: OptionalState[RuntimeVariantID] = field(
        default_factory=OptionalState[RuntimeVariantID].nop
    )

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.deployment_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_group.update_dict(to_update, "resource_group")
        self.replicas.update_dict(to_update, "replicas")
        return to_update

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()

    def replica_count_modified(self) -> bool:
        return self.replicas.optional_value() is not None

    def has_revision_changes(self) -> bool:
        return any([
            self.resource_slots.optional_value() is not None,
            self.resource_opts.optional_value() is not None,
            self.cluster_mode.optional_value() is not None,
            self.cluster_size.optional_value() is not None,
            self.image.optional_value() is not None,
            self.model_definition_path.optional_value() is not None,
            self.extra_mounts.optional_value() is not None,
            self.environ.optional_value() is not None,
            self.runtime_variant_id.optional_value() is not None,
        ])


@dataclass
class EndpointLifecycleBatchUpdater(DataBatchUpdater[EndpointRow, DeploymentInfo]):
    """Advances the lifecycle of every named deployment still in one of the
    ``lifecycle_stages``.

    Each axis is independently optional; ``None`` means "do not touch this
    column". ``sub_step`` is coupled to ``lifecycle_stage`` — it is written
    (possibly to ``None``, clearing a leftover sub-step) only when the lifecycle
    advances, so a scaling-only transition leaves a DEPLOYING endpoint's
    sub-step alone.
    """

    deployment_ids: Sequence[DeploymentID]
    lifecycle_stages: Sequence[EndpointLifecycle] = ()
    lifecycle_stage: EndpointLifecycle | None = None
    sub_step: DeploymentLifecycleSubStep | None = None
    scaling_state: ScalingState | None = None

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def conditions(self) -> list[QueryCondition]:
        conditions = [DeploymentConditions.by_ids(list(self.deployment_ids))]
        if self.lifecycle_stages:
            conditions.append(DeploymentConditions.by_lifecycle_stages(list(self.lifecycle_stages)))
        return conditions

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if self.lifecycle_stage is not None:
            values["lifecycle_stage"] = self.lifecycle_stage
            values["sub_step"] = self.sub_step
        if self.scaling_state is not None:
            values["scaling_state"] = self.scaling_state
        return values

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()


@dataclass
class AutoScalingRuleUpdater(DataUpdater[EndpointAutoScalingRuleRow, EndpointAutoScalingRuleData]):
    """Edits one auto-scaling rule of a deployment."""

    rule_id: RuleId
    metric_source: OptionalState[AutoScalingMetricSource] = field(default_factory=OptionalState.nop)
    metric_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    threshold: OptionalState[Decimal] = field(default_factory=OptionalState.nop)
    comparator: OptionalState[AutoScalingMetricComparator] = field(
        default_factory=OptionalState.nop
    )
    step_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    cooldown_seconds: OptionalState[int] = field(default_factory=OptionalState.nop)
    min_replicas: TriState[int] = field(default_factory=TriState.nop)
    max_replicas: TriState[int] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[EndpointAutoScalingRuleRow]:
        return EndpointAutoScalingRuleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointAutoScalingRuleRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.rule_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.metric_source.update_dict(to_update, "metric_source")
        self.metric_name.update_dict(to_update, "metric_name")
        # The legacy threshold+comparator pair maps onto the min/max columns.
        threshold_val = self.threshold.optional_value()
        comparator_val = self.comparator.optional_value()
        if threshold_val is not None and comparator_val is not None:
            if comparator_val in (
                AutoScalingMetricComparator.GREATER_THAN,
                AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL,
            ):
                to_update["max_threshold"] = threshold_val
            else:
                to_update["min_threshold"] = threshold_val
        elif threshold_val is not None:
            to_update["max_threshold"] = threshold_val
        self.step_size.update_dict(to_update, "step_size")
        self.cooldown_seconds.update_dict(to_update, "cooldown_seconds")
        self.min_replicas.update_dict(to_update, "min_replicas")
        self.max_replicas.update_dict(to_update, "max_replicas")
        return to_update

    @override
    def to_data(self, row: EndpointAutoScalingRuleRow) -> EndpointAutoScalingRuleData:
        return row.to_data()


@dataclass
class DeploymentRolloutClearUpdater(DataBatchUpdater[EndpointRow, DeploymentInfo]):
    """Clears the rollout pointer and sub-step of each deployment whose rollout ended."""

    deployment_ids: Sequence[DeploymentID]

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [DeploymentConditions.by_ids(list(self.deployment_ids))]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"target_replica_group_id": None, "sub_step": None}

    @override
    def to_data(self, row: EndpointRow) -> DeploymentInfo:
        return row.to_bare_deployment_info()
