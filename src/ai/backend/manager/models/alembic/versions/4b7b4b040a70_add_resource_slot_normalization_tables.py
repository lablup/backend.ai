"""add_resource_slot_normalization_tables

Revision ID: 4b7b4b040a70
Revises: bc4e0e948300
Create Date: 2026-02-08 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "4b7b4b040a70"
down_revision = "bc4e0e948300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. resource_slot_types
    op.create_table(
        "resource_slot_types",
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("slot_type", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("slot_name", name=op.f("pk_resource_slot_types")),
    )

    # 2. agent_resources
    op.create_table(
        "agent_resources",
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("capacity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column("used", sa.Numeric(precision=24, scale=6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("agent_id", "slot_name", name=op.f("pk_agent_resources")),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_agent_resources_agent_id_agents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name=op.f("fk_agent_resources_slot_name_resource_slot_types"),
        ),
    )
    op.create_index(
        op.f("ix_agent_resources_slot_name"),
        "agent_resources",
        ["slot_name"],
        unique=False,
    )
    op.create_index(
        "ix_agent_resources_agent_avail",
        "agent_resources",
        ["agent_id", "slot_name", "capacity", "used"],
        unique=False,
    )

    # 3. resource_allocations
    op.create_table(
        "resource_allocations",
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("requested", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column("used", sa.Numeric(precision=24, scale=6), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("kernel_id", "slot_name", name=op.f("pk_resource_allocations")),
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name=op.f("fk_resource_allocations_kernel_id_kernels"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name=op.f("fk_resource_allocations_slot_name_resource_slot_types"),
        ),
    )
    op.create_index(
        op.f("ix_resource_allocations_slot_name"),
        "resource_allocations",
        ["slot_name"],
        unique=False,
    )
    op.create_index(
        "ix_ra_kernel_slot",
        "resource_allocations",
        ["kernel_id", "slot_name"],
        unique=False,
    )

    # 4. Seed data for resource_slot_types
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO resource_slot_types
                (slot_name, slot_type, display_name, rank)
            VALUES
                ('cpu', 'count', 'CPU', 40),
                ('mem', 'bytes', 'Memory', 50),
                ('cuda.device', 'count', 'GPU (CUDA)', 10),
                ('cuda.shares', 'count', 'GPU (fGPU)', 20),
                ('rocm.device', 'count', 'GPU (ROCm)', 30),
                ('tpu.device', 'count', 'TPU', 35)
        """)
    )

    # 5. Backfill: register any unknown slot names from agents and kernels
    conn.execute(
        sa.text("""
            INSERT INTO resource_slot_types (slot_name, slot_type, rank)
            SELECT DISTINCT kv.key, 'count', 0
            FROM agents a, jsonb_each_text(a.available_slots) AS kv(key, value)
            WHERE a.status = 'ALIVE'
              AND kv.key NOT IN (SELECT slot_name FROM resource_slot_types)
            ON CONFLICT (slot_name) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO resource_slot_types (slot_name, slot_type, rank)
            SELECT DISTINCT req.key, 'count', 0
            FROM kernels k, jsonb_each_text(k.requested_slots) AS req(key, value)
            WHERE k.status NOT IN ('TERMINATED', 'CANCELLED')
              AND req.key NOT IN (SELECT slot_name FROM resource_slot_types)
            ON CONFLICT (slot_name) DO NOTHING
        """)
    )

    # 6. Backfill agent_resources from agents JSONB columns
    conn.execute(
        sa.text("""
            INSERT INTO agent_resources
                (agent_id, slot_name, capacity, used)
            SELECT a.id, kv.key, kv.value::numeric(24,6), occ.value::numeric(24,6)
            FROM agents a,
                 jsonb_each_text(a.available_slots) AS kv(key, value)
            LEFT JOIN jsonb_each_text(a.occupied_slots) AS occ(key, value)
                 ON kv.key = occ.key
            WHERE a.status = 'ALIVE'
              AND kv.key IN (SELECT slot_name FROM resource_slot_types)
            ON CONFLICT (agent_id, slot_name) DO NOTHING
        """)
    )

    # 7. Backfill resource_allocations from kernels JSONB columns
    conn.execute(
        sa.text("""
            INSERT INTO resource_allocations
                (kernel_id, slot_name, requested, used)
            SELECT k.id, req.key, req.value::numeric(24,6), occ.value::numeric(24,6)
            FROM kernels k,
                 jsonb_each_text(k.requested_slots) AS req(key, value)
            LEFT JOIN jsonb_each_text(k.occupied_slots) AS occ(key, value)
                 ON req.key = occ.key
            WHERE k.status NOT IN ('TERMINATED', 'CANCELLED')
              AND req.key IN (SELECT slot_name FROM resource_slot_types)
            ON CONFLICT (kernel_id, slot_name) DO NOTHING
        """)
    )


def downgrade() -> None:
    op.drop_index("ix_ra_kernel_slot", table_name="resource_allocations")
    op.drop_index(op.f("ix_resource_allocations_slot_name"), table_name="resource_allocations")
    op.drop_table("resource_allocations")
    op.drop_index("ix_agent_resources_agent_avail", table_name="agent_resources")
    op.drop_index(
        op.f("ix_agent_resources_slot_name"),
        table_name="agent_resources",
    )
    op.drop_table("agent_resources")
    op.drop_table("resource_slot_types")
