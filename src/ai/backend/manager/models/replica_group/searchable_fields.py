"""What a replica group search can filter and order by, and how a group row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.deployment.types import (
    ReplicaGroupData,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _ReplicaGroupOwnFields(RowDataConverter[ReplicaGroupRow, ReplicaGroupData]):
    """The replica group's own columns. ``rollout`` is JSON, so both slots stay empty."""

    field_id = SearchableField(
        ReplicaGroupRow.id, UUIDConditions(ReplicaGroupRow.id), ColumnOrder(ReplicaGroupRow.id)
    )
    deployment_id = SearchableField(
        ReplicaGroupRow.deployment_id,
        UUIDConditions(ReplicaGroupRow.deployment_id),
        ColumnOrder(ReplicaGroupRow.deployment_id),
    )
    current_revision_id = SearchableField(
        ReplicaGroupRow.current_revision_id,
        UUIDConditions(ReplicaGroupRow.current_revision_id),
        ColumnOrder(ReplicaGroupRow.current_revision_id),
    )
    target_revision_id = SearchableField(
        ReplicaGroupRow.target_revision_id,
        UUIDConditions(ReplicaGroupRow.target_revision_id),
        ColumnOrder(ReplicaGroupRow.target_revision_id),
    )
    desired_current_replica_count = SearchableField(
        ReplicaGroupRow.desired_current_replica_count,
        IntConditions(ReplicaGroupRow.desired_current_replica_count),
        ColumnOrder(ReplicaGroupRow.desired_current_replica_count),
    )
    desired_target_replica_count = SearchableField(
        ReplicaGroupRow.desired_target_replica_count,
        IntConditions(ReplicaGroupRow.desired_target_replica_count),
        ColumnOrder(ReplicaGroupRow.desired_target_replica_count),
    )
    traffic_weight = SearchableField(
        ReplicaGroupRow.traffic_weight,
        IntConditions(ReplicaGroupRow.traffic_weight),
        ColumnOrder(ReplicaGroupRow.traffic_weight),
    )
    session_group_id = SearchableField(
        ReplicaGroupRow.session_group_id,
        UUIDConditions(ReplicaGroupRow.session_group_id),
        ColumnOrder(ReplicaGroupRow.session_group_id),
    )
    lifecycle = SearchableField(
        ReplicaGroupRow.lifecycle,
        EnumConditions(ReplicaGroupRow.lifecycle, ReplicaGroupLifecycle),
        ColumnOrder(ReplicaGroupRow.lifecycle),
    )
    scaling_status = SearchableField(
        ReplicaGroupRow.scaling_status,
        EnumConditions(ReplicaGroupRow.scaling_status, ReplicaGroupScalingStatus),
        ColumnOrder(ReplicaGroupRow.scaling_status),
    )
    created_at = SearchableField(
        ReplicaGroupRow.created_at,
        DateTimeConditions(ReplicaGroupRow.created_at),
        ColumnOrder(ReplicaGroupRow.created_at),
    )
    updated_at = SearchableField(
        ReplicaGroupRow.updated_at,
        DateTimeConditions(ReplicaGroupRow.updated_at),
        ColumnOrder(ReplicaGroupRow.updated_at),
    )
    rollout = SearchableField(ReplicaGroupRow.rollout, None, None)

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return ReplicaGroupData(
            id=self.field_id.read(row),
            deployment_id=self.deployment_id.read(row),
            current_revision_id=self.current_revision_id.read(row),
            target_revision_id=self.target_revision_id.read(row),
            desired_current_replica_count=self.desired_current_replica_count.read(row),
            desired_target_replica_count=self.desired_target_replica_count.read(row),
            traffic_weight=self.traffic_weight.read(row),
            session_group_id=self.session_group_id.read(row),
            lifecycle=self.lifecycle.read(row),
            scaling_status=self.scaling_status.read(row),
            rollout=self.rollout.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _ReplicaGroupNestedFields:
    """The revisions the group points at. Both are the same deployment's field rows."""

    current_revision = NestedSearchableField(
        ModelRevisionSearchableFields.own,
        ToOneCorrelation(
            DeploymentRevisionRow,
            ReplicaGroupRow,
            DeploymentRevisionRow.id == ReplicaGroupRow.current_revision_id,
        ),
    )
    target_revision = NestedSearchableField(
        ModelRevisionSearchableFields.own,
        ToOneCorrelation(
            DeploymentRevisionRow,
            ReplicaGroupRow,
            DeploymentRevisionRow.id == ReplicaGroupRow.target_revision_id,
        ),
    )


class ReplicaGroupSearchableFields:
    own = _ReplicaGroupOwnFields()
    nested = _ReplicaGroupNestedFields
