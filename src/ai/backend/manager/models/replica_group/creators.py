"""Creator specs for the replica_groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.schema.deployment import ReplicaGroupRolloutSpec
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupData,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ReplicaGroupCreator(FieldCreator[DeploymentID, ReplicaGroupRow, ReplicaGroupData]):
    """Adds a replica group to the deployment whose replicas it holds."""

    session_group_id: SessionGroupID
    rollout: ReplicaGroupRolloutSpec
    lifecycle: ReplicaGroupLifecycle = ReplicaGroupLifecycle.STABLE
    scaling_status: ReplicaGroupScalingStatus = ReplicaGroupScalingStatus.STABLE
    traffic_weight: int = 100
    current_revision_id: DeploymentRevisionID | None = None
    target_revision_id: DeploymentRevisionID | None = None
    desired_current_replica_count: int = 0
    desired_target_replica_count: int = 0

    @classmethod
    def for_primary(
        cls,
        session_group_id: SessionGroupID,
        rollout: ReplicaGroupRolloutSpec,
        desired_current_replica_count: int,
    ) -> ReplicaGroupCreator:
        """The group a deployment starts with: it serves all traffic and holds no
        rollout target until the first one begins."""
        return cls(
            session_group_id=session_group_id,
            rollout=rollout,
            desired_current_replica_count=desired_current_replica_count,
        )

    @classmethod
    def for_rollout_target(
        cls,
        session_group_id: SessionGroupID,
        rollout: ReplicaGroupRolloutSpec,
        target_revision_id: DeploymentRevisionID,
        desired_target_replica_count: int,
    ) -> ReplicaGroupCreator:
        """The group a blue-green or canary rollout fills: it takes no traffic
        until it is promoted."""
        return cls(
            session_group_id=session_group_id,
            rollout=rollout,
            lifecycle=ReplicaGroupLifecycle.ROLLING,
            scaling_status=ReplicaGroupScalingStatus.SCALING,
            traffic_weight=0,
            target_revision_id=target_revision_id,
            desired_target_replica_count=desired_target_replica_count,
        )

    @override
    def field_id(self, row: ReplicaGroupRow) -> ReplicaGroupID:
        return ReplicaGroupID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> ReplicaGroupRow:
        return ReplicaGroupRow(
            deployment_id=owner_id,
            session_group_id=self.session_group_id,
            current_revision_id=self.current_revision_id,
            target_revision_id=self.target_revision_id,
            lifecycle=self.lifecycle,
            scaling_status=self.scaling_status,
            traffic_weight=self.traffic_weight,
            desired_current_replica_count=self.desired_current_replica_count,
            desired_target_replica_count=self.desired_target_replica_count,
            rollout=self.rollout,
        )

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()
