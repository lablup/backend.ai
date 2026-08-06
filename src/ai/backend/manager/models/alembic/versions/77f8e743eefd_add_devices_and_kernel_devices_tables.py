"""add devices and kernel_devices tables

Revision ID: 77f8e743eefd
Revises: 2dccb3069031
Create Date: 2026-08-05 13:57:55.984027

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

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
        sa.PrimaryKeyConstraint("agent_uuid", "device_name", "device_id", name=op.f("pk_devices")),
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name=op.f("fk_devices_agent_uuid_agents"),
            ondelete="CASCADE",
        ),
    )
    op.create_table(
        "kernel_devices",
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("agent_uuid", GUID(), nullable=False),
        sa.Column("device_name", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column(
            "data",
            pgsql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "kernel_id", "agent_uuid", "device_name", "device_id", name=op.f("pk_kernel_devices")
        ),
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name=op.f("fk_kernel_devices_kernel_id_kernels"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_uuid", "device_name", "device_id"],
            ["devices.agent_uuid", "devices.device_name", "devices.device_id"],
            name=op.f("fk_kernel_devices_device_devices"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_kernel_devices_device"),
        "kernel_devices",
        ["agent_uuid", "device_name", "device_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_kernel_devices_device"), table_name="kernel_devices")
    op.drop_table("kernel_devices")
    op.drop_table("devices")
