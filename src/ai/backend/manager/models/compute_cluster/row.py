from __future__ import annotations

from datetime import datetime
from typing import Final

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import ComputeClusterStatus
from ai.backend.manager.models.base import GUID, Base, SecretColumn, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.secret.types import SecretValue

COMPUTE_CLUSTER_KUBECONFIG_CONTEXT: Final[str] = "compute_clusters.kubeconfig"


class ComputeClusterRow(LifecycleTimestampsMixin, Base):
    """A Kubernetes cluster that runs the sessions of `driver = "kubernetes"` resource groups."""

    __tablename__ = "compute_clusters"

    id: Mapped[ComputeClusterID] = mapped_column(
        "id",
        GUID(ComputeClusterID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[str] = mapped_column(sa.String(length=64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(sa.String(length=512), nullable=True)
    api_server: Mapped[str] = mapped_column(sa.String(length=2048), nullable=False)
    kubeconfig: Mapped[SecretValue] = mapped_column(
        SecretColumn(COMPUTE_CLUSTER_KUBECONFIG_CONTEXT), nullable=False
    )
    namespace_prefix: Mapped[str] = mapped_column(
        sa.String(length=32), nullable=False, server_default="bai-"
    )
    gateway_addr: Mapped[str | None] = mapped_column(sa.String(length=256), nullable=True)
    gateway_public_key: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[ComputeClusterStatus] = mapped_column(
        StrEnumType(ComputeClusterStatus, length=16),
        nullable=False,
        server_default=ComputeClusterStatus.UNKNOWN.value,
    )
    status_changed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
