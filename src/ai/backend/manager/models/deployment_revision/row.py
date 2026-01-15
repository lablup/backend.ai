from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    RuntimeVariant,
    VFolderMount,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    EnvironmentVariableEntryData,
    ExtraVFolderMountData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    ResourceConfigData,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
    URLColumn,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow
    from ai.backend.manager.models.image import ImageRow
    from ai.backend.manager.models.routing import RoutingRow

__all__ = ("DeploymentRevisionRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


def _get_endpoint_join_condition():
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(DeploymentRevisionRow.endpoint) == EndpointRow.id


def _get_image_join_condition():
    from ai.backend.manager.models.image import ImageRow

    return foreign(DeploymentRevisionRow.image) == ImageRow.id


def _get_routings_join_condition():
    from ai.backend.manager.models.routing import RoutingRow

    return DeploymentRevisionRow.id == foreign(RoutingRow.revision)


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

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[uuid.UUID] = mapped_column("endpoint", GUID, nullable=False)
    revision_number: Mapped[int] = mapped_column("revision_number", sa.Integer, nullable=False)

    # Image configuration
    image: Mapped[uuid.UUID] = mapped_column("image", GUID, nullable=False)

    # Model configuration
    model: Mapped[uuid.UUID | None] = mapped_column("model", GUID, nullable=True)
    model_mount_destination: Mapped[str] = mapped_column(
        "model_mount_destination",
        sa.String(length=1024),
        nullable=False,
        default="/models",
        server_default="/models",
    )
    model_definition_path: Mapped[str | None] = mapped_column(
        "model_definition_path", sa.String(length=128), nullable=True
    )
    model_definition: Mapped[dict | None] = mapped_column(
        "model_definition", pgsql.JSONB(), nullable=True
    )

    # Resource configuration
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False
    )
    resource_slots: Mapped[ResourceSlot] = mapped_column(
        "resource_slots", ResourceSlotColumn(), nullable=False
    )
    resource_opts: Mapped[dict] = mapped_column(
        "resource_opts", pgsql.JSONB(), nullable=False, default={}, server_default="{}"
    )

    # Cluster configuration
    cluster_mode: Mapped[str] = mapped_column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size: Mapped[int] = mapped_column(
        "cluster_size", sa.Integer, nullable=False, default=1, server_default="1"
    )

    # Execution configuration
    startup_command: Mapped[str | None] = mapped_column("startup_command", sa.Text, nullable=True)
    bootstrap_script: Mapped[str | None] = mapped_column(
        "bootstrap_script", sa.String(length=16 * 1024), nullable=True
    )
    environ: Mapped[dict] = mapped_column(
        "environ", pgsql.JSONB(), nullable=False, default={}, server_default="{}"
    )
    callback_url: Mapped[str | None] = mapped_column(
        "callback_url", URLColumn, nullable=True, default=sa.null()
    )
    runtime_variant: Mapped[RuntimeVariant] = mapped_column(
        "runtime_variant",
        StrEnumType(RuntimeVariant),
        nullable=False,
        default=RuntimeVariant.CUSTOM,
    )

    # Mount configuration
    extra_mounts: Mapped[list[VFolderMount]] = mapped_column(
        "extra_mounts",
        StructuredJSONObjectListColumn(VFolderMount),
        nullable=False,
        default=[],
        server_default="[]",
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships (without FK constraints)
    endpoint_row: Mapped[EndpointRow] = relationship(
        "EndpointRow",
        back_populates="revisions",
        primaryjoin=_get_endpoint_join_condition,
    )
    image_row: Mapped[ImageRow] = relationship(
        "ImageRow",
        primaryjoin=_get_image_join_condition,
    )
    routings: Mapped[list[RoutingRow]] = relationship(
        "RoutingRow",
        primaryjoin=_get_routings_join_condition,
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
                environ=[
                    EnvironmentVariableEntryData(name=k, value=v) for k, v in self.environ.items()
                ]
                if self.environ
                else None,
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
                    mount_destination=str(mount.kernel_path),
                )
                for mount in (self.extra_mounts or [])
            ],
        )
