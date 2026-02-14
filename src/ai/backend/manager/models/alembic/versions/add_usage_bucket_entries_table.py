"""add_usage_bucket_entries_table

Revision ID: ba4308_usage_entries
Revises: ccf8ae5c90fe
Create Date: 2026-02-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ba4308_usage_entries"
down_revision = "ccf8ae5c90fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usage_bucket_entries",
        sa.Column("bucket_id", GUID(), nullable=False),
        sa.Column("bucket_type", sa.String(length=16), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("bucket_id", "slot_name", name=op.f("pk_usage_bucket_entries")),
    )
    op.create_index(
        "ix_usage_bucket_entries_slot",
        "usage_bucket_entries",
        ["slot_name"],
        unique=False,
    )
    op.create_index(
        "ix_usage_bucket_entries_bucket_type",
        "usage_bucket_entries",
        ["bucket_type"],
        unique=False,
    )

    # Data migration: decompose existing JSONB resource_usage into normalized rows
    conn = op.get_bind()

    # Migrate domain usage buckets
    _migrate_bucket_table(conn, "domain_usage_buckets", "domain")

    # Migrate project usage buckets
    _migrate_bucket_table(conn, "project_usage_buckets", "project")

    # Migrate user usage buckets
    _migrate_bucket_table(conn, "user_usage_buckets", "user")


def _migrate_bucket_table(conn: sa.engine.Connection, table_name: str, bucket_type: str) -> None:
    """Migrate existing JSONB resource_usage to normalized usage_bucket_entries rows."""
    rows = conn.execute(
        sa.text(
            f"SELECT id, resource_usage, capacity_snapshot, "
            f"period_start, period_end FROM {table_name}"
        )
    ).fetchall()

    for row in rows:
        bucket_id = row[0]
        resource_usage = row[1] or {}
        capacity_snapshot = row[2] or {}
        period_start = row[3]
        period_end = row[4]

        # Calculate duration in seconds from period dates
        if period_start and period_end:
            duration_days = (period_end - period_start).days
            # For same-day buckets, use 1 day as minimum
            if duration_days <= 0:
                duration_days = 1
            duration_seconds = duration_days * 86400
        else:
            duration_seconds = 86400  # default 1 day

        for slot_name, resource_seconds_value in resource_usage.items():
            try:
                resource_seconds = float(resource_seconds_value)
            except (ValueError, TypeError):
                continue

            if resource_seconds == 0 or duration_seconds == 0:
                continue

            # Decompose: amount = resource_seconds / duration_seconds
            amount = resource_seconds / duration_seconds
            capacity = float(capacity_snapshot.get(slot_name, 0))

            conn.execute(
                sa.text(
                    "INSERT INTO usage_bucket_entries "
                    "(bucket_id, bucket_type, slot_name, amount, duration_seconds, capacity) "
                    "VALUES (:bucket_id, :bucket_type, :slot_name, :amount, :duration_seconds, :capacity) "
                    "ON CONFLICT (bucket_id, slot_name) DO NOTHING"
                ),
                {
                    "bucket_id": bucket_id,
                    "bucket_type": bucket_type,
                    "slot_name": slot_name,
                    "amount": amount,
                    "duration_seconds": duration_seconds,
                    "capacity": capacity,
                },
            )


def downgrade() -> None:
    op.drop_index("ix_usage_bucket_entries_bucket_type", table_name="usage_bucket_entries")
    op.drop_index("ix_usage_bucket_entries_slot", table_name="usage_bucket_entries")
    op.drop_table("usage_bucket_entries")
