from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.config import PresetModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
    PydanticListColumn,
    ResourceOptsEntry,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.models.runtime_variant_preset.types import (
    RuntimeVariantPresetValueEntry,
)

__all__ = ("DeploymentRevisionPresetRow",)


class DeploymentRevisionPresetRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "deployment_revision_presets"

    __table_args__ = (
        sa.UniqueConstraint(
            "runtime_variant", "name", name="uq_deployment_revision_presets_variant_name"
        ),
        sa.Index("ix_deployment_revision_presets_variant_rank", "runtime_variant", "rank"),
    )

    id: Mapped[DeploymentPresetID] = mapped_column(
        "id",
        GUID(DeploymentPresetID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    runtime_variant: Mapped[RuntimeVariantID] = mapped_column(
        "runtime_variant", GUID(RuntimeVariantID), nullable=False
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    rank: Mapped[int] = mapped_column("rank", sa.Integer, nullable=False)

    image_id: Mapped[ImageID] = mapped_column("image_id", GUID(ImageID), nullable=False)
    model_definition: Mapped[PresetModelDefinition | None] = mapped_column(
        "model_definition", PydanticColumn(PresetModelDefinition, exclude_unset=True), nullable=True
    )
    resource_opts: Mapped[list[ResourceOptsEntry]] = mapped_column(
        "resource_opts", PydanticListColumn(ResourceOptsEntry), nullable=False, server_default="[]"
    )
    cluster_mode: Mapped[str] = mapped_column(
        "cluster_mode", sa.String(length=16), nullable=False, server_default="single-node"
    )
    cluster_size: Mapped[int] = mapped_column(
        "cluster_size", sa.Integer, nullable=False, server_default="1"
    )
    startup_command: Mapped[str | None] = mapped_column("startup_command", sa.Text, nullable=True)
    bootstrap_script: Mapped[str | None] = mapped_column("bootstrap_script", sa.Text, nullable=True)
    environ: Mapped[dict[str, str]] = mapped_column(
        "environ", pgsql.JSONB(), nullable=False, default={}, server_default="{}"
    )
    preset_values: Mapped[list[RuntimeVariantPresetValueEntry]] = mapped_column(
        "preset_values",
        PydanticListColumn(RuntimeVariantPresetValueEntry),
        nullable=False,
        server_default="[]",
    )

    # Deployment-level preset fields. ``open_to_public`` and
    # ``revision_history_limit`` stay nullable: deployment creation has
    # safe system defaults for them. ``replica_count`` /
    # ``deployment_strategy`` / ``deployment_strategy_spec`` are
    # ``nullable=False`` because deployment creation requires concrete
    # values for all three.
    open_to_public: Mapped[bool | None] = mapped_column(
        "open_to_public", sa.Boolean(), nullable=True
    )
    replica_count: Mapped[int] = mapped_column(
        "replica_count", sa.Integer(), nullable=False, server_default="1"
    )
    revision_history_limit: Mapped[int | None] = mapped_column(
        "revision_history_limit", sa.Integer(), nullable=True
    )
    deployment_strategy: Mapped[DeploymentStrategy] = mapped_column(
        "deployment_strategy",
        StrEnumType(DeploymentStrategy, use_name=False),
        nullable=False,
        server_default="ROLLING",
    )
    deployment_strategy_spec: Mapped[dict[str, object]] = mapped_column(
        "deployment_strategy_spec",
        pgsql.JSONB(),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )
