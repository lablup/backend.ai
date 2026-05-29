from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow
    from ai.backend.manager.models.routing import RoutingRow

__all__ = ("ReplicaGroupRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_deployment_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(ReplicaGroupRow.deployment_id) == EndpointRow.id


def _get_replicas_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.routing import RoutingRow

    return ReplicaGroupRow.id == foreign(RoutingRow.replica_group_id)


class ReplicaGroupRow(Base):  # type: ignore[misc]
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
        server_default=sa.text("uuid_generate_v4()"),
    )
    deployment_id: Mapped[DeploymentID] = mapped_column(
        "deployment_id",
        GUID,
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

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    endpoint_row: Mapped[EndpointRow] = relationship(
        "EndpointRow",
        primaryjoin=_get_deployment_join_condition,
        viewonly=True,
    )
    replicas: Mapped[list[RoutingRow]] = relationship(
        "RoutingRow",
        primaryjoin=_get_replicas_join_condition,
        viewonly=True,
    )
