"""add_device_metadata_to_resource_slot_types

Revision ID: ccf8ae5c90fe
Revises: f41bbe0c0f12
Create Date: 2026-02-12 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "ccf8ae5c90fe"
down_revision = "f41bbe0c0f12"
branch_labels = None
depends_on = None

# Slot types that did NOT exist in the original seed (6 original: cpu, mem,
# cuda.device, cuda.shares, rocm.device, tpu.device).
_new_slot_names = (
    "ipu.device",
    "atom.device",
    "atom-plus.device",
    "atom-max.device",
    "gaudi2.device",
    "warboy.device",
    "rngd.device",
    "hyperaccel-lpu.device",
)


def upgrade() -> None:
    # 1. Add new columns as nullable first (existing rows need defaults)
    op.add_column(
        "resource_slot_types",
        sa.Column("description", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "resource_slot_types",
        sa.Column("display_unit", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "resource_slot_types",
        sa.Column("display_icon", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "resource_slot_types",
        sa.Column("number_format", pgsql.JSONB(), nullable=True),
    )

    # 2. Upsert all 14 slot types (6 existing + 8 new) with full metadata
    # Use exec_driver_sql to avoid sa.text() parsing JSON colons as bind params
    conn = op.get_bind()
    conn.exec_driver_sql("""
        INSERT INTO resource_slot_types
            (slot_name, slot_type, display_name, description,
             display_unit, display_icon, number_format, rank)
        VALUES
            ('cpu',        'count', 'CPU',        'CPU',
             'Core',    'cpu',     '{"binary":false,"round_length":0}', 100),
            ('mem',        'bytes', 'RAM',        'Memory',
             'GiB',     'ram',     '{"binary":true,"round_length":0}',  200),
            ('cuda.device','count', 'GPU',        'CUDA-capable GPU',
             'GPU',     'nvidia',  '{"binary":false,"round_length":0}', 300),
            ('cuda.shares','count', 'fGPU',       'CUDA-capable GPU (fractional)',
             'fGPU',    'nvidia',  '{"binary":false,"round_length":2}', 400),
            ('rocm.device','count', 'GPU',        'ROCm-capable GPU',
             'GPU',     'rocm',    '{"binary":false,"round_length":0}', 500),
            ('tpu.device', 'count', 'TPU',        'TPU device',
             'GPU',     'tpu',     '{"binary":false,"round_length":0}', 600),
            ('ipu.device', 'count', 'IPU',        'IPU device',
             'IPU',     'ipu',     '{"binary":false,"round_length":0}', 700),
            ('atom.device','count', 'ATOM Device','ATOM',
             'ATOM',    'rebel',   '{"binary":false,"round_length":0}', 800),
            ('atom-plus.device','count','ATOM+ Device','ATOM+',
             'ATOM+',   'rebel',   '{"binary":false,"round_length":0}', 900),
            ('atom-max.device','count','ATOM Max Device','ATOM Max',
             'ATOM Max','rebel',   '{"binary":false,"round_length":0}', 1000),
            ('gaudi2.device','count','Gaudi 2 Device','Gaudi 2',
             'Gaudi 2', 'gaudi',   '{"binary":false,"round_length":0}', 1100),
            ('warboy.device','count','Warboy Device','Furiosa Warboy',
             'Warboy',  'furiosa', '{"binary":false,"round_length":0}', 1200),
            ('rngd.device','count', 'RNGD Device','Furiosa RNGD',
             'RNGD',    'furiosa', '{"binary":false,"round_length":0}', 1300),
            ('hyperaccel-lpu.device','count','Hyperaccel LPU Device','Hyperaccel LPU',
             'LPU',     'lpu',     '{"binary":false,"round_length":0}', 1400)
        ON CONFLICT (slot_name) DO UPDATE SET
            display_name  = EXCLUDED.display_name,
            description   = EXCLUDED.description,
            display_unit  = EXCLUDED.display_unit,
            display_icon  = EXCLUDED.display_icon,
            number_format = EXCLUDED.number_format,
            rank          = EXCLUDED.rank
    """)

    # 3. Fill defaults for any dynamically-registered rows not covered by upsert
    conn.exec_driver_sql("""
        UPDATE resource_slot_types
        SET description  = COALESCE(description, ''),
            display_unit = COALESCE(display_unit, ''),
            display_icon = COALESCE(display_icon, ''),
            number_format = COALESCE(number_format, '{"binary":false,"round_length":0}'::jsonb)
        WHERE description IS NULL
           OR display_unit IS NULL
           OR display_icon IS NULL
           OR number_format IS NULL
    """)

    # 4. Also make display_name NOT NULL (was nullable before)
    conn.exec_driver_sql("""
        UPDATE resource_slot_types
        SET display_name = COALESCE(display_name, '')
        WHERE display_name IS NULL
    """)

    # 5. Set columns to NOT NULL with server defaults
    op.alter_column(
        "resource_slot_types",
        "display_name",
        nullable=False,
        server_default=sa.text("''"),
    )
    op.alter_column(
        "resource_slot_types",
        "description",
        nullable=False,
        server_default=sa.text("''"),
    )
    op.alter_column(
        "resource_slot_types",
        "display_unit",
        nullable=False,
        server_default=sa.text("''"),
    )
    op.alter_column(
        "resource_slot_types",
        "display_icon",
        nullable=False,
        server_default=sa.text("''"),
    )
    op.alter_column(
        "resource_slot_types",
        "number_format",
        nullable=False,
        server_default=sa.text(r"""'{"binary"\:false,"round_length"\:0}'::jsonb"""),
    )


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Delete newly added slot types (keep original 6)
    conn.execute(
        sa.text("DELETE FROM resource_slot_types WHERE slot_name = ANY(:names)"),
        {"names": list(_new_slot_names)},
    )

    # 2. Revert original 6 display_name and rank values; restore display_name nullable
    conn.exec_driver_sql("""
        UPDATE resource_slot_types SET display_name = v.display_name, rank = v.rank
        FROM (VALUES
            ('cpu',         'CPU',        40),
            ('mem',         'Memory',     50),
            ('cuda.device', 'GPU (CUDA)', 10),
            ('cuda.shares', 'GPU (fGPU)', 20),
            ('rocm.device', 'GPU (ROCm)', 30),
            ('tpu.device',  'TPU',        35)
        ) AS v(slot_name, display_name, rank)
        WHERE resource_slot_types.slot_name = v.slot_name
    """)
    op.alter_column("resource_slot_types", "display_name", nullable=True, server_default=None)

    # 3. Drop new columns
    op.drop_column("resource_slot_types", "number_format")
    op.drop_column("resource_slot_types", "display_icon")
    op.drop_column("resource_slot_types", "display_unit")
    op.drop_column("resource_slot_types", "description")
