"""CreatorSpecs for replica group inserts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.schema.deployment import ReplicaGroupRolloutSpec
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ReplicaGroupCreatorSpec(CreatorSpec[ReplicaGroupRow]):
    deployment_id: DeploymentID
    target_revision_id: DeploymentRevisionID
    desired_target_replica_count: int
    rollout: ReplicaGroupRolloutSpec

    @override
    def build_row(self) -> ReplicaGroupRow:
        return ReplicaGroupRow(
            deployment_id=self.deployment_id,
            target_revision_id=self.target_revision_id,
            lifecycle=ReplicaGroupLifecycle.ROLLING,
            scaling_status=ReplicaGroupScalingStatus.SCALING,
            traffic_weight=0,
            desired_target_replica_count=self.desired_target_replica_count,
            rollout=self.rollout,
        )
