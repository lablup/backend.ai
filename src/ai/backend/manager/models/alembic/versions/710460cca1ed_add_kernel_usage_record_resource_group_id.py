"""add kernel usage record resource_group_id column

Add a non-null ``resource_group_id`` column alongside the existing
``resource_group`` name column, backfill rows whose names still resolve,
and remove orphan rows that cannot be resolved. The name-based lookup
behavior remains unchanged during this expand phase.

The table is copied into a new one that carries the column, and only rows whose
names resolve are copied, instead of updating and deleting rows in place.

Revision ID: 710460cca1ed
Revises: 097389c0853b
Create Date: 2026-07-14

"""

from alembic import op

from ai.backend.manager.models.alembic.kernel_usage_record_rebuild import KernelUsageRecordRebuild

revision = "710460cca1ed"
down_revision = "097389c0853b"
# Part of: 26.8.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    rebuild = KernelUsageRecordRebuild(op.get_bind())
    if "resource_group_id" not in rebuild.columns():
        rebuild.run()


def downgrade() -> None:
    op.drop_column("kernel_usage_records", "resource_group_id")
