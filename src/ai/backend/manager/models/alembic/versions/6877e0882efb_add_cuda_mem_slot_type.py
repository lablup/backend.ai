"""Register the cuda.mem slot type for fractional GPU memory allocation."""

from alembic import op

revision = "6877e0882efb"
down_revision = "a31e8d4c9b72"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_REFERENCING_TABLES = (
    "agent_resources",
    "resource_allocations",
    "model_card_resource_requirements",
    "preset_resource_slots",
    "deployment_revision_resource_slots",
)


def upgrade() -> None:
    op.get_bind().exec_driver_sql("""
        INSERT INTO resource_slot_types
            (slot_name, slot_type, display_name, description,
             display_unit, display_icon, number_format, rank)
        VALUES
            ('cuda.mem', 'bytes', 'GPU Memory', 'CUDA-capable GPU memory (fractional)',
             'GiB', 'nvidia', '{"binary":true,"round_length":1}', 450)
        ON CONFLICT (slot_name) DO NOTHING
    """)


def downgrade() -> None:
    referenced = " AND ".join(
        f"NOT EXISTS (SELECT 1 FROM {table} WHERE slot_name = 'cuda.mem')"
        for table in _REFERENCING_TABLES
    )
    op.get_bind().exec_driver_sql(
        f"DELETE FROM resource_slot_types WHERE slot_name = 'cuda.mem' AND {referenced}"
    )
