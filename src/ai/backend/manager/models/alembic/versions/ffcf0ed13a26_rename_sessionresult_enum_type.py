"""rename sessionresults enum type to sessionresult

Revision ID: ffcf0ed13a26
Revises: 03ff6767b2e4
Create Date: 2026-02-25 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ffcf0ed13a26"
down_revision = "03ff6767b2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Unify the enum type name to "sessionresult" (singular)
    # Some databases have "sessionresults" (plural) from 2022 migration (b6b884fbae1f)
    # This migration renames plural to singular to match database convention
    conn = op.get_bind()

    # Check if both types exist (edge case: database has both enum types)
    result_singular = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresult'")
    has_singular = result_singular.fetchone() is not None

    result_plural = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresults'")
    has_plural = result_plural.fetchone() is not None

    if has_plural and not has_singular:
        # Normal case: plural exists, rename it to singular
        conn.exec_driver_sql("ALTER TYPE sessionresults RENAME TO sessionresult")
    # If both exist, skip rename to avoid conflict
    # If only singular exists, no action needed


def downgrade() -> None:
    # Revert to plural form
    # Only attempt if singular form exists and plural does not
    conn = op.get_bind()

    result_singular = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresult'")
    has_singular = result_singular.fetchone() is not None

    result_plural = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresults'")
    has_plural = result_plural.fetchone() is not None

    if has_singular and not has_plural:
        # Normal case: singular exists, rename it to plural
        conn.exec_driver_sql("ALTER TYPE sessionresult RENAME TO sessionresults")
    # If both exist, skip rename to avoid conflict
    # If only plural exists, no action needed
