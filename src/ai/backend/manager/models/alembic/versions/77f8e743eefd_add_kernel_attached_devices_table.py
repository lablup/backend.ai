"""add kernel_attached_devices table

Revision ID: 77f8e743eefd
Revises: c1a7d3f05e28
Create Date: 2026-08-05 13:57:55.984027

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "77f8e743eefd"
down_revision = "c1a7d3f05e28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kernel_attached_devices",
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("device_name", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
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
            "kernel_id", "device_name", "device_id", name=op.f("pk_kernel_attached_devices")
        ),
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name=op.f("fk_kernel_attached_devices_kernel_id_kernels"),
            ondelete="CASCADE",
        ),
    )
    # Backfill from kernels.attached_devices; the CASE guards keep the SRFs
    # safe against non-object / non-array values, and the capacity map is
    # normalized to a [{"name", "value"}] entry array with non-number values
    # dropped.
    op.execute("""\
        INSERT INTO kernel_attached_devices (kernel_id, device_name, device_id, model_name, data)
        SELECT
            k.id,
            dev.key,
            elem->>'device_id',
            coalesce(elem->>'model_name', ''),
            coalesce(
                (SELECT jsonb_agg(jsonb_build_object('name', c.key, 'value', c.value))
                 FROM jsonb_each(
                     CASE WHEN jsonb_typeof(elem->'data') = 'object'
                          THEN elem->'data' ELSE '{}'::jsonb END
                 ) AS c
                 WHERE jsonb_typeof(c.value) = 'number'),
                '[]'::jsonb
            )
        FROM kernels k,
            jsonb_each(
                CASE WHEN jsonb_typeof(k.attached_devices) = 'object'
                     THEN k.attached_devices ELSE '{}'::jsonb END
            ) AS dev,
            jsonb_array_elements(
                CASE WHEN jsonb_typeof(dev.value) = 'array'
                     THEN dev.value ELSE '[]'::jsonb END
            ) AS elem
        WHERE elem->>'device_id' IS NOT NULL
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("kernel_attached_devices")
