"""Resource Slot Normalization Row models.

Database models for normalized resource slot management:
- ResourceSlotTypeRow: Registry of known resource slot types and display metadata
- AgentResourceRow: Per-agent, per-slot resource capacity and usage
- ResourceAllocationRow: Per-kernel, per-slot resource allocation
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.deployment_revision_resource_slot import (
    DeploymentRevisionResourceSlotID,
)
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.model_card_resource_requirement import (
    ModelCardResourceRequirementID,
)
from ai.backend.common.data.entity.preset_resource_slot import PresetResourceSlotID
from ai.backend.common.data.entity.resource_allocation import ResourceAllocationID
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.manager.data.resource_slot.types import (
    NumberFormatData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin, LifecycleTimestampsMixin
from ai.backend.manager.models.resource_slot.types import NumberFormat

__all__ = (
    "ResourceSlotTypeRow",
    "AgentResourceRow",
    "ResourceAllocationRow",
    "ModelCardResourceRequirementRow",
    "PresetResourceSlotRow",
    "DeploymentRevisionResourceSlotRow",
)


class ResourceSlotTypeRow(LifecycleTimestampsMixin, Base):
    """Registry of known resource slot types with display metadata.

    Primary key is slot_name (e.g., 'cpu', 'mem', 'cuda.device').
    """

    __tablename__ = "resource_slot_types"

    uuid: Mapped[ResourceSlotTypeUUID] = mapped_column(
        "uuid",
        GUID(ResourceSlotTypeUUID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    slot_type: Mapped[str] = mapped_column("slot_type", sa.String(length=16), nullable=False)
    required: Mapped[bool] = mapped_column(
        "required",
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.false(),
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled",
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.true(),
    )
    display_name: Mapped[str] = mapped_column(
        "display_name",
        sa.String(length=128),
        nullable=False,
        default="",
        server_default=sa.text("''"),
    )
    description: Mapped[str] = mapped_column(
        "description",
        sa.String(length=256),
        nullable=False,
        default="",
        server_default=sa.text("''"),
    )
    display_unit: Mapped[str] = mapped_column(
        "display_unit",
        sa.String(length=32),
        nullable=False,
        default="",
        server_default=sa.text("''"),
    )
    display_icon: Mapped[str] = mapped_column(
        "display_icon",
        sa.String(length=64),
        nullable=False,
        default="",
        server_default=sa.text("''"),
    )
    number_format: Mapped[NumberFormat] = mapped_column(
        "number_format",
        PydanticColumn(NumberFormat),
        nullable=False,
        default=NumberFormat(),
        server_default=sa.text(r"""'{"binary"\:false,"round_length"\:0}'::jsonb"""),
    )
    rank: Mapped[int] = mapped_column(
        "rank", sa.Integer, nullable=False, server_default=sa.text("0")
    )

    def to_data(self) -> ResourceSlotTypeData:
        return ResourceSlotTypeData(
            uuid=self.uuid,
            slot_name=self.slot_name,
            slot_type=self.slot_type,
            required=self.required,
            enabled=self.enabled,
            display_name=self.display_name,
            description=self.description,
            display_unit=self.display_unit,
            display_icon=self.display_icon,
            number_format=NumberFormatData(
                binary=self.number_format.binary,
                round_length=self.number_format.round_length,
            ),
            rank=self.rank,
        )


class AgentResourceRow(LifecycleTimestampsMixin, Base):
    """Per-agent, per-slot resource capacity and usage.

    Composite primary key: (agent_id, slot_name).
    """

    __tablename__ = "agent_resources"

    id: Mapped[AgentResourceID] = mapped_column(
        "id",
        GUID(AgentResourceID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    agent_id: Mapped[str] = mapped_column("agent_id", sa.String(length=64), primary_key=True)
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    capacity: Mapped[Decimal] = mapped_column(
        "capacity", sa.Numeric(precision=24, scale=6), nullable=False
    )
    reserved: Mapped[Decimal] = mapped_column(
        "reserved", sa.Numeric(precision=24, scale=6), nullable=False, server_default=sa.text("0")
    )
    prereserved: Mapped[Decimal] = mapped_column(
        "prereserved",
        sa.Numeric(precision=24, scale=6),
        nullable=False,
        server_default=sa.text("0"),
    )
    used: Mapped[Decimal] = mapped_column(
        "used", sa.Numeric(precision=24, scale=6), nullable=False, server_default=sa.text("0")
    )

    slot_type_row: Mapped[ResourceSlotTypeRow] = relationship(
        "ResourceSlotTypeRow", foreign_keys=[slot_name], lazy="raise"
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_resources_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_agent_resources_slot_name_resource_slot_types",
        ),
        sa.Index("ix_agent_resources_slot_name", "slot_name"),
        sa.Index(
            "ix_agent_resources_agent_avail",
            "agent_id",
            "slot_name",
            "capacity",
            "reserved",
            "used",
        ),
    )


class ResourceAllocationRow(CreatedAtMixin, Base):
    """Per-kernel, per-slot resource allocation.

    Composite primary key: (kernel_id, slot_name).
    """

    __tablename__ = "resource_allocations"

    id: Mapped[ResourceAllocationID] = mapped_column(
        "id",
        GUID(ResourceAllocationID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    kernel_id: Mapped[KernelID] = mapped_column("kernel_id", GUID(KernelID), primary_key=True)
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    requested: Mapped[Decimal] = mapped_column(
        "requested", sa.Numeric(precision=24, scale=6), nullable=False
    )
    prereserved: Mapped[Decimal] = mapped_column(
        "prereserved",
        sa.Numeric(precision=24, scale=6),
        nullable=False,
        server_default=sa.text("0"),
    )
    reserved: Mapped[Decimal] = mapped_column(
        "reserved",
        sa.Numeric(precision=24, scale=6),
        nullable=False,
        server_default=sa.text("0"),
    )
    used: Mapped[Decimal | None] = mapped_column(
        "used", sa.Numeric(precision=24, scale=6), nullable=True
    )
    prereserved_at: Mapped[datetime | None] = mapped_column(
        "prereserved_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )
    reserved_at: Mapped[datetime | None] = mapped_column(
        "reserved_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        "used_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )
    free_at: Mapped[datetime | None] = mapped_column(
        "free_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name="fk_resource_allocations_kernel_id_kernels",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_resource_allocations_slot_name_resource_slot_types",
        ),
        sa.Index("ix_resource_allocations_slot_name", "slot_name"),
        sa.Index("ix_ra_kernel_slot", "kernel_id", "slot_name"),
        sa.Index(
            "ix_ra_occupied",
            "kernel_id",
            "slot_name",
            postgresql_where=sa.text("free_at IS NULL"),
        ),
    )


class ModelCardResourceRequirementRow(Base):
    """Per-model-card, per-slot minimum resource requirement.

    Composite primary key: (model_card_id, slot_name).
    """

    __tablename__ = "model_card_resource_requirements"

    id: Mapped[ModelCardResourceRequirementID] = mapped_column(
        "id",
        GUID(ModelCardResourceRequirementID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    model_card_id: Mapped[ModelCardID] = mapped_column(
        "model_card_id", GUID(ModelCardID), primary_key=True
    )
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    min_quantity: Mapped[Decimal] = mapped_column(
        "min_quantity", sa.Numeric(precision=24, scale=6), nullable=False
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["model_card_id"],
            ["model_cards.id"],
            name="fk_mc_resource_req_model_card_id_model_cards",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_mc_resource_req_slot_name_resource_slot_types",
        ),
        sa.Index("ix_mc_resource_req_slot_name", "slot_name"),
    )


class PresetResourceSlotRow(Base):
    """Per-preset, per-slot resource allocation.

    Composite primary key: (preset_id, slot_name).
    """

    __tablename__ = "preset_resource_slots"

    id: Mapped[PresetResourceSlotID] = mapped_column(
        "id",
        GUID(PresetResourceSlotID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    preset_id: Mapped[DeploymentPresetID] = mapped_column(
        "preset_id", GUID(DeploymentPresetID), primary_key=True
    )
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(
        "quantity", sa.Numeric(precision=24, scale=6), nullable=False
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["preset_id"],
            ["deployment_revision_presets.id"],
            name="fk_preset_resource_slots_preset_id_drp",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_preset_resource_slots_slot_name_resource_slot_types",
        ),
        sa.Index("ix_preset_resource_slots_slot_name", "slot_name"),
    )


class DeploymentRevisionResourceSlotRow(Base):
    """Per-revision, per-slot resource allocation.

    Composite primary key: (revision_id, slot_name).
    """

    __tablename__ = "deployment_revision_resource_slots"

    id: Mapped[DeploymentRevisionResourceSlotID] = mapped_column(
        "id",
        GUID(DeploymentRevisionResourceSlotID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v4()"),
    )
    revision_id: Mapped[DeploymentRevisionID] = mapped_column(
        "revision_id", GUID(DeploymentRevisionID), primary_key=True
    )
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(
        "quantity", sa.Numeric(precision=24, scale=6), nullable=False
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["deployment_revisions.id"],
            name="fk_dr_resource_slots_revision_id_deployment_revisions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_dr_resource_slots_slot_name_resource_slot_types",
        ),
        sa.Index("ix_dr_resource_slots_slot_name", "slot_name"),
    )
