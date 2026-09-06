"""Update specs for the replica_groups table, split by deploy / scaling concern."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupData,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ReplicaGroupDeployUpdater(DataUpdater[ReplicaGroupRow, ReplicaGroupData]):
    """Deploy-axis update: revision pointers, rollout lifecycle, traffic weight."""

    replica_group_id: ReplicaGroupID
    # Revision pointers are nullable; ``TriState`` so a rollback can NULL them explicitly.
    current_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    target_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    lifecycle: OptionalState[ReplicaGroupLifecycle] = field(default_factory=OptionalState.nop)
    traffic_weight: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReplicaGroupRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.replica_group_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.current_revision_id.update_dict(values, "current_revision_id")
        self.target_revision_id.update_dict(values, "target_revision_id")
        self.lifecycle.update_dict(values, "lifecycle")
        self.traffic_weight.update_dict(values, "traffic_weight")
        return values

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()


@dataclass
class ReplicaGroupScalingUpdater(DataUpdater[ReplicaGroupRow, ReplicaGroupData]):
    """Scaling-axis update: desired replica counts and scaling status."""

    replica_group_id: ReplicaGroupID
    desired_current_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    desired_target_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    scaling_status: OptionalState[ReplicaGroupScalingStatus] = field(
        default_factory=OptionalState.nop
    )

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReplicaGroupRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.replica_group_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.desired_current_replica_count.update_dict(values, "desired_current_replica_count")
        self.desired_target_replica_count.update_dict(values, "desired_target_replica_count")
        self.scaling_status.update_dict(values, "scaling_status")
        return values

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()


@dataclass
class ReplicaGroupLifecycleUpdater(DataUpdater[ReplicaGroupRow, ReplicaGroupData]):
    """Lifecycle-reconcile update: the rolling/draining step writes both axes at once —
    the next desired counts + scaling status (re-arm scaling) and the lifecycle transition."""

    replica_group_id: ReplicaGroupID
    lifecycle: OptionalState[ReplicaGroupLifecycle] = field(default_factory=OptionalState.nop)
    desired_current_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    desired_target_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    scaling_status: OptionalState[ReplicaGroupScalingStatus] = field(
        default_factory=OptionalState.nop
    )
    # On rollout convergence the group promotes its target revision to current and clears target.
    current_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    target_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReplicaGroupRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.replica_group_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.lifecycle.update_dict(values, "lifecycle")
        self.desired_current_replica_count.update_dict(values, "desired_current_replica_count")
        self.desired_target_replica_count.update_dict(values, "desired_target_replica_count")
        self.scaling_status.update_dict(values, "scaling_status")
        self.current_revision_id.update_dict(values, "current_revision_id")
        self.target_revision_id.update_dict(values, "target_revision_id")
        return values

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()


@dataclass
class ReplicaGroupRevisionSwapUpdater(DataBatchUpdater[ReplicaGroupRow, ReplicaGroupData]):
    """Rolls each named deployment's primary group forward: the revision it was
    rolling out becomes the one it serves."""

    deployment_ids: Collection[DeploymentID]

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def conditions(self) -> list[QueryCondition]:
        deployment_ids = list(self.deployment_ids)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            primary_group_ids = sa.select(EndpointRow.primary_replica_group_id).where(
                EndpointRow.id.in_(deployment_ids)
            )
            return sa.and_(
                ReplicaGroupRow.id.in_(primary_group_ids),
                ReplicaGroupRow.target_revision_id.is_not(None),
            )

        return [inner]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {
            "current_revision_id": ReplicaGroupRow.target_revision_id,
            "target_revision_id": None,
        }

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()
