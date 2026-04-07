from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    EnvironEntryData,
    PresetValueData,
    ResourceOptsEntryData,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
    PydanticListColumn,
    ResourceOptsEntry,
    StrEnumType,
)
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow

__all__ = ("DeploymentRevisionPresetRow",)


class DeploymentRevisionPresetRow(Base):  # type: ignore[misc]
    __tablename__ = "deployment_revision_presets"

    __table_args__ = (
        sa.UniqueConstraint(
            "runtime_variant", "name", name="uq_deployment_revision_presets_variant_name"
        ),
        sa.Index("ix_deployment_revision_presets_variant_rank", "runtime_variant", "rank"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    runtime_variant: Mapped[uuid.UUID] = mapped_column("runtime_variant", GUID, nullable=False)
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    rank: Mapped[int] = mapped_column("rank", sa.Integer, nullable=False)

    image_id: Mapped[uuid.UUID] = mapped_column("image_id", GUID, nullable=False)
    model_definition: Mapped[ModelDefinition | None] = mapped_column(
        "model_definition", PydanticColumn(ModelDefinition), nullable=True
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
    preset_values: Mapped[list[PresetValueEntry]] = mapped_column(
        "preset_values", PydanticListColumn(PresetValueEntry), nullable=False, server_default="[]"
    )

    # Deployment-level preset fields (nullable: None means "preset does not specify,
    # fall back to user input or system default").
    open_to_public: Mapped[bool | None] = mapped_column(
        "open_to_public", sa.Boolean(), nullable=True
    )
    replica_count: Mapped[int | None] = mapped_column("replica_count", sa.Integer(), nullable=True)
    revision_history_limit: Mapped[int | None] = mapped_column(
        "revision_history_limit", sa.Integer(), nullable=True
    )
    deployment_strategy: Mapped[DeploymentStrategy | None] = mapped_column(
        "deployment_strategy",
        StrEnumType(DeploymentStrategy, use_name=False),
        nullable=True,
    )
    deployment_strategy_spec: Mapped[dict[str, object] | None] = mapped_column(
        "deployment_strategy_spec",
        pgsql.JSONB(),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.now(),
    )

    resource_slot_rows: Mapped[list[PresetResourceSlotRow]] = relationship(
        "PresetResourceSlotRow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_data(self) -> DeploymentRevisionPresetData:
        return DeploymentRevisionPresetData(
            id=self.id,
            runtime_variant_id=self.runtime_variant,
            name=self.name,
            description=self.description,
            rank=self.rank,
            image_id=self.image_id,
            model_definition=(
                self.model_definition.model_dump(by_alias=True, exclude_none=True)
                if self.model_definition
                else None
            ),
            resource_opts=[
                ResourceOptsEntryData(name=e.name, value=e.value)
                for e in (self.resource_opts or [])
            ],
            cluster_mode=self.cluster_mode,
            cluster_size=self.cluster_size,
            startup_command=self.startup_command,
            bootstrap_script=self.bootstrap_script,
            environ=[EnvironEntryData(key=k, value=v) for k, v in (self.environ or {}).items()],
            preset_values=[
                PresetValueData(preset_id=pv.preset_id, value=pv.value)
                for pv in (self.preset_values or [])
            ],
            open_to_public=self.open_to_public,
            replica_count=self.replica_count,
            revision_history_limit=self.revision_history_limit,
            deployment_strategy=self.deployment_strategy,
            deployment_strategy_spec=self.deployment_strategy_spec,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
