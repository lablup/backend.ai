from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
import yarl
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.config import ModelDefinition
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetValueData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
    PydanticListColumn,
    StrEnumType,
    URLColumn,
)
from ai.backend.manager.models.runtime_variant_preset.types import RuntimeVariantPresetValueEntry

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow
    from ai.backend.manager.models.image import ImageRow
    from ai.backend.manager.models.resource_slot.row import DeploymentRevisionResourceSlotRow
    from ai.backend.manager.models.routing import RoutingRow
    from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow

__all__ = ("DeploymentRevisionRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _get_endpoint_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(DeploymentRevisionRow.endpoint) == EndpointRow.id


def _get_image_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.image import ImageRow

    return foreign(DeploymentRevisionRow.image) == ImageRow.id


def _get_runtime_variant_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow

    return foreign(DeploymentRevisionRow.runtime_variant_id) == RuntimeVariantRow.id


def _get_routings_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    from ai.backend.manager.models.routing import RoutingRow

    return DeploymentRevisionRow.id == foreign(RoutingRow.revision)


class DeploymentRevisionRow(Base):  # type: ignore[misc]
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

    id: Mapped[DeploymentRevisionID] = mapped_column(
        "id",
        GUID(DeploymentRevisionID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    endpoint: Mapped[DeploymentID] = mapped_column("endpoint", GUID, nullable=False)
    revision_number: Mapped[int] = mapped_column("revision_number", sa.Integer, nullable=False)

    # Image configuration.
    # ``image IS NULL`` after the image row is deleted (SET NULL FK). The
    # revision is kept for history but cannot be redeployed in that state
    # — a new revision pointing at a live image must take over.
    image: Mapped[ImageID | None] = mapped_column(
        "image",
        GUID(ImageID),
        sa.ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Model vfolder.
    # ``model IS NULL`` after the backing vfolder is deleted (SET NULL FK);
    # same semantics as ``image``.
    model: Mapped[VFolderUUID | None] = mapped_column(
        "model",
        GUID(VFolderUUID),
        sa.ForeignKey("vfolders.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_mount_destination: Mapped[str] = mapped_column(
        "model_mount_destination",
        sa.String(length=1024),
        nullable=False,
        default="/models",
        server_default="/models",
    )
    # Subpath within the model vfolder. ``NULL`` (default) mounts the
    # vfolder root; same semantics as ``MountInfoEntry.subpath`` for
    # extra mounts.
    vfolder_subpath: Mapped[str | None] = mapped_column(
        "vfolder_subpath", sa.String(length=1024), nullable=True
    )
    model_definition_path: Mapped[str | None] = mapped_column(
        "model_definition_path", sa.String(length=128), nullable=True
    )
    model_definition: Mapped[ModelDefinition | None] = mapped_column(
        "model_definition", PydanticColumn(ModelDefinition), nullable=True
    )
    # Resolved permission for the model vfolder mount, frozen at
    # revision-write time. ``NULL`` for rows written before this column
    # existed; the draft builder falls back to READ_ONLY for those.
    model_mount_perm: Mapped[MountPermission | None] = mapped_column(
        "model_mount_perm", StrEnumType(MountPermission), nullable=True
    )

    # Resource configuration
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False
    )
    resource_opts: Mapped[dict[str, Any]] = mapped_column(
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
    environ: Mapped[dict[str, Any]] = mapped_column(
        "environ", pgsql.JSONB(), nullable=False, default={}, server_default="{}"
    )
    callback_url: Mapped[str | None] = mapped_column(
        "callback_url", URLColumn, nullable=True, default=sa.null()
    )
    runtime_variant_id: Mapped[RuntimeVariantID] = mapped_column(
        "runtime_variant_id",
        GUID(RuntimeVariantID),
        sa.ForeignKey("runtime_variants.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Seconds to keep a route's session alive after its traffic is drained,
    # so in-flight requests can finish before the kernel is killed.
    termination_grace_period: Mapped[float] = mapped_column(
        "termination_grace_period",
        sa.Float,
        nullable=False,
        default=30.0,
        server_default="30",
    )

    # Mount configuration.
    # Stores only the fields that session creation actually consumes
    # (``vfolder_id``, ``mount_destination``, ``mount_perm``, ``subpath``);
    # the other ``VFolderMount`` fields (``name``, ``host_path``,
    # ``usage_mode``) are re-derived by ``prepare_vfolder_mounts`` at each
    # session creation, so persisting them would only be dead weight.
    extra_mounts: Mapped[list[MountInfoEntry]] = mapped_column(
        "extra_mounts",
        PydanticListColumn(MountInfoEntry),
        nullable=False,
        default=[],
        server_default="[]",
    )

    # Runtime variant preset values (resolved at session creation time)
    preset_values: Mapped[list[RuntimeVariantPresetValueEntry]] = mapped_column(
        "preset_values",
        PydanticListColumn(RuntimeVariantPresetValueEntry),
        nullable=False,
        default=[],
        server_default="[]",
    )

    # Deployment-level preset reference. ``NULL`` after the referenced
    # preset row is deleted (SET NULL FK), and on legacy rows that
    # predate this column. The materialised effects of the preset live
    # on ``preset_values`` and the resolved configuration columns; this
    # field exists so the original preset selection can be recovered
    # when the client edits the revision.
    revision_preset_id: Mapped[DeploymentPresetID | None] = mapped_column(
        "revision_preset_id",
        GUID(DeploymentPresetID),
        sa.ForeignKey("deployment_revision_presets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Normalized resource slot rows
    resource_slot_rows: Mapped[list[DeploymentRevisionResourceSlotRow]] = relationship(
        "DeploymentRevisionResourceSlotRow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    endpoint_row: Mapped[EndpointRow] = relationship(
        "EndpointRow",
        back_populates="revisions",
        primaryjoin=_get_endpoint_join_condition,
    )
    image_row: Mapped[ImageRow] = relationship(
        "ImageRow",
        primaryjoin=_get_image_join_condition,
    )
    runtime_variant_row: Mapped[RuntimeVariantRow] = relationship(
        "RuntimeVariantRow",
        primaryjoin=_get_runtime_variant_join_condition,
        lazy="joined",
        innerjoin=True,
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
            deployment_id=self.endpoint,
            revision_number=self.revision_number,
            created_at=self.created_at,
            image_id=self.image,
            cluster_config=ClusterConfigData(
                mode=ClusterMode(self.cluster_mode),
                size=self.cluster_size,
            ),
            resource_config=ResourceConfigData(
                resource_group_name=self.resource_group,
                resource_slot=ResourceSlot({
                    r.slot_name: r.quantity for r in self.resource_slot_rows
                }),
                resource_opts=self.resource_opts or {},
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(self.runtime_variant_id),
                environ=self.environ,
                runtime_variant_preset_values=[
                    RuntimeVariantPresetValueData(preset_id=pv.preset_id, value=pv.value)
                    for pv in (self.preset_values or [])
                ],
            ),
            execution=ExecutionData(
                startup_command=self.startup_command,
                bootstrap_script=self.bootstrap_script,
                callback_url=yarl.URL(self.callback_url) if self.callback_url else None,
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=self.model,
                mount_destination=self.model_mount_destination,
                subpath=self.vfolder_subpath,
                definition_path=self.model_definition_path or "",
                extra_mounts=list(self.extra_mounts),
                model_mount_perm=self.model_mount_perm,
            ),
            revision_preset=PresetAttributionData(
                preset_id=self.revision_preset_id,
                # DeploymentRevisionPresetData is not stored on the row
                # value fields are not used, currently dead code
                values=[],
            ),
            model_definition=self.model_definition,
        )
