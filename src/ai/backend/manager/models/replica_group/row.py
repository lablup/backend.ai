from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.schema.deployment import ReplicaGroupRolloutSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupData,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.base import GUID, Base, PydanticColumn, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.views.replica_group import (
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupScalingSchedulingView,
)

__all__ = ("ReplicaGroupRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReplicaGroupRow(LifecycleTimestampsMixin, Base):
    """
    A group of replicas (routes) within a single deployment.

    A replica group owns the revision pointers and per-revision desired
    replica counts so a deployment can run several groups, each rolling
    out its own revision and receiving a share of the traffic.
    """

    __tablename__ = "replica_groups"

    __table_args__ = (sa.Index("ix_replica_groups_deployment_id", "deployment_id"),)

    id: Mapped[ReplicaGroupID] = mapped_column(
        "id",
        GUID(ReplicaGroupID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    deployment_id: Mapped[DeploymentID] = mapped_column(
        "deployment_id",
        GUID(DeploymentID),
        sa.ForeignKey("endpoints.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Revision pointers (no FK; mirrors ``RoutingRow.revision``).
    # ``current_revision_id`` is the revision actively serving traffic in
    # this group; ``target_revision_id`` is the revision being rolled out
    # within the group (``NULL`` when no rollout is in progress).
    current_revision_id: Mapped[DeploymentRevisionID | None] = mapped_column(
        "current_revision_id", GUID(DeploymentRevisionID), nullable=True
    )
    target_revision_id: Mapped[DeploymentRevisionID | None] = mapped_column(
        "target_revision_id", GUID(DeploymentRevisionID), nullable=True
    )

    # Desired replica counts split by revision within the group.
    desired_current_replica_count: Mapped[int] = mapped_column(
        "desired_current_replica_count",
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    desired_target_replica_count: Mapped[int] = mapped_column(
        "desired_target_replica_count",
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )

    # Relative weight of this group when distributing traffic across the
    # deployment's replica groups. Defaults to 100 so a lone group receives
    # the full share and percentage-style splits are intuitive.
    traffic_weight: Mapped[int] = mapped_column(
        "traffic_weight",
        sa.Integer,
        nullable=False,
        default=100,
        server_default=sa.text("100"),
    )

    # The placement group shared by this group's route sessions (1:1 — a
    # replica group always owns exactly one). `use_alter` keeps the FK out of
    # the CREATE TABLE so table subsets that omit ``session_groups`` still build.
    session_group_id: Mapped[SessionGroupID] = mapped_column(
        "session_group_id",
        GUID(SessionGroupID),
        sa.ForeignKey(
            "session_groups.id",
            use_alter=True,
            name="fk_replica_groups_session_group_id_session_groups",
        ),
        nullable=False,
    )

    lifecycle: Mapped[ReplicaGroupLifecycle] = mapped_column(
        "lifecycle",
        StrEnumType(ReplicaGroupLifecycle),
        nullable=False,
        default=ReplicaGroupLifecycle.STABLE,
        server_default=ReplicaGroupLifecycle.STABLE.value,
    )
    scaling_status: Mapped[ReplicaGroupScalingStatus] = mapped_column(
        "scaling_status",
        StrEnumType(ReplicaGroupScalingStatus),
        nullable=False,
        default=ReplicaGroupScalingStatus.STABLE,
        server_default=ReplicaGroupScalingStatus.STABLE.value,
    )
    rollout: Mapped[ReplicaGroupRolloutSpec] = mapped_column(
        "rollout",
        PydanticColumn(ReplicaGroupRolloutSpec),
        nullable=False,
    )

    def to_data(self) -> ReplicaGroupData:
        return ReplicaGroupData(
            id=self.id,
            deployment_id=self.deployment_id,
            current_revision_id=self.current_revision_id,
            target_revision_id=self.target_revision_id,
            desired_current_replica_count=self.desired_current_replica_count,
            desired_target_replica_count=self.desired_target_replica_count,
            traffic_weight=self.traffic_weight,
            session_group_id=self.session_group_id,
            lifecycle=self.lifecycle,
            scaling_status=self.scaling_status,
            rollout=self.rollout,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_deploy_scheduling_view(self) -> ReplicaGroupDeploySchedulingView:
        return ReplicaGroupDeploySchedulingView(
            group_id=self.id,
            deployment_id=self.deployment_id,
            current_revision_id=self.current_revision_id,
            target_revision_id=self.target_revision_id,
            lifecycle=self.lifecycle,
            traffic_weight=self.traffic_weight,
        )

    def to_scaling_scheduling_view(self) -> ReplicaGroupScalingSchedulingView:
        return ReplicaGroupScalingSchedulingView(
            group_id=self.id,
            deployment_id=self.deployment_id,
            desired_current_replica_count=self.desired_current_replica_count,
            desired_target_replica_count=self.desired_target_replica_count,
            scaling_status=self.scaling_status,
        )
