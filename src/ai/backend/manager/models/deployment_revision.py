from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import relationship

from ai.backend.common.types import (
    ClusterMode,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.logging import BraceStyleAdapter

from ..data.deployment.types import (
    ClusterConfigData,
    ExtraVFolderMountData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ResourceConfigData,
)
from .base import (
    GUID,
    Base,
    IDColumn,
    ResourceSlotColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
)

if TYPE_CHECKING:
    from .routing import RoutingRow

__all__ = ("DeploymentRevisionRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class DeploymentRevisionRow(Base):
    """
    Represents a deployment revision (K8s ReplicaSet equivalent).

    Each revision captures a snapshot of the deployment configuration at a point in time.
    When the configuration changes (image, resources, etc.), a new revision is created.
    The endpoint's current_revision points to the active revision.
    """

    __tablename__ = "deployment_revisions"

    __table_args__ = (
        sa.UniqueConstraint(
            "endpoint",
            "revision_number",
            name="uq_deployment_revisions_endpoint_revision_number",
        ),
        sa.Index("ix_deployment_revisions_endpoint", "endpoint"),
    )

    id = IDColumn()
    endpoint = sa.Column("endpoint", GUID, nullable=False)
    revision_number = sa.Column("revision_number", sa.Integer, nullable=False)

    # Image configuration
    image = sa.Column("image", GUID, nullable=False)

    # Model configuration
    model = sa.Column("model", GUID, nullable=True)
    model_mount_destination = sa.Column(
        "model_mount_destination",
        sa.String(length=1024),
        nullable=False,
        default="/models",
        server_default="/models",
    )
    model_definition_path = sa.Column("model_definition_path", sa.String(length=128), nullable=True)
    model_definition = sa.Column("model_definition", pgsql.JSONB(), nullable=True)

    # Resource configuration
    resource_group = sa.Column("resource_group", sa.String(length=64), nullable=False)
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    resource_opts = sa.Column(
        "resource_opts", pgsql.JSONB(), nullable=False, default={}, server_default="{}"
    )

    # Cluster configuration
    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size = sa.Column(
        "cluster_size", sa.Integer, nullable=False, default=1, server_default="1"
    )

    # Execution configuration
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    environ = sa.Column("environ", pgsql.JSONB(), nullable=False, default={}, server_default="{}")
    callback_url = sa.Column("callback_url", URLColumn, nullable=True, default=sa.null())
    runtime_variant = sa.Column(
        "runtime_variant",
        StrEnumType(RuntimeVariant),
        nullable=False,
        default=RuntimeVariant.CUSTOM,
    )

    # Mount configuration
    extra_mounts = sa.Column(
        "extra_mounts",
        StructuredJSONObjectListColumn(VFolderMount),
        nullable=False,
        default=[],
        server_default="[]",
    )

    # Metadata
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships (without FK constraints)
    endpoint_row = relationship(
        "EndpointRow",
        back_populates="revisions",
        primaryjoin="foreign(DeploymentRevisionRow.endpoint) == EndpointRow.id",
    )
    image_row = relationship(
        "ImageRow",
        primaryjoin="foreign(DeploymentRevisionRow.image) == ImageRow.id",
    )
    routings: list["RoutingRow"] = relationship(
        "RoutingRow",
        primaryjoin="DeploymentRevisionRow.id == foreign(RoutingRow.revision)",
        viewonly=True,
    )

    def to_data(self) -> ModelRevisionData:
        """Convert to ModelRevisionData dataclass."""
        return ModelRevisionData(
            id=self.id,
            name=f"revision-{self.revision_number}",
            cluster_config=ClusterConfigData(
                mode=ClusterMode(self.cluster_mode),
                size=self.cluster_size,
            ),
            resource_config=ResourceConfigData(
                resource_group_name=self.resource_group,
                resource_slot=self.resource_slots,
                resource_opts=self.resource_opts or {},
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant=self.runtime_variant,
                environ=self.environ,
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=self.model,
                mount_destination=self.model_mount_destination,
                definition_path=self.model_definition_path or "",
            ),
            created_at=self.created_at,
            image_id=self.image,
            extra_vfolder_mounts=[
                ExtraVFolderMountData(
                    vfolder_id=mount.vfid.folder_id,
                    mount_destination=mount.kernel_path,
                )
                for mount in (self.extra_mounts or [])
            ],
        )
