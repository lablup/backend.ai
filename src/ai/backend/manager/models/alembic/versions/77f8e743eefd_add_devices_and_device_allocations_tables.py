"""add devices and device_allocations tables

Revision ID: 77f8e743eefd
Revises: 2dccb3069031
Create Date: 2026-08-05 13:57:55.984027

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "77f8e743eefd"
down_revision = "2dccb3069031"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("agent_uuid", GUID(), nullable=False),
        sa.Column("device_name", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_devices")),
        sa.UniqueConstraint(
            "agent_uuid", "device_name", "device_id", name=op.f("uq_devices_agent_device")
        ),
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name=op.f("fk_devices_agent_uuid_agents"),
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "device_allocations",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("device_uuid", GUID(), nullable=False),
        sa.Column("capacity_name", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_allocations")),
        sa.UniqueConstraint(
            "kernel_id",
            "device_uuid",
            "capacity_name",
            name=op.f("uq_device_allocations_kernel_device_capacity"),
        ),
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name=op.f("fk_device_allocations_kernel_id_kernels"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_uuid"],
            ["devices.id"],
            name=op.f("fk_device_allocations_device_uuid_devices"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_device_allocations_device_uuid"),
        "device_allocations",
        ["device_uuid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_device_allocations_device_uuid"), table_name="device_allocations")
    op.drop_table("device_allocations")
    op.drop_table("devices")
