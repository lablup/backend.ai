"""rename sessionresult enum type

Revision ID: ffcf0ed13a26
Revises: ffcf0ed13a25
Create Date: 2026-02-25 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ffcf0ed13a26"
down_revision = "ffcf0ed13a25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Unify the enum type name to "sessionresults" (plural)
    # Old databases have "sessionresult" (singular) from 2019 migration (405aa2c39458)
    # New databases have "sessionresults" (plural) from 2022 migration (b6b884fbae1f)
    # This migration renames singular to plural if needed
    conn = op.get_bind()
    result = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresult'")
    if result.fetchone() is not None:
        # Old enum type exists, rename it
        conn.exec_driver_sql("ALTER TYPE sessionresult RENAME TO sessionresults")


def downgrade() -> None:
    # Revert to singular form
    # Only attempt if plural form exists
    conn = op.get_bind()
    result = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresults'")
    if result.fetchone() is not None:
        conn.exec_driver_sql("ALTER TYPE sessionresults RENAME TO sessionresult")
