"""fix sessionresult enum type when both singular and plural coexist

Revision ID: 0b1efbb2db84
Revises: 7h4m7ygnaao1
Create Date: 2026-03-05 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0b1efbb2db84"
down_revision = "7h4m7ygnaao1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    result_singular = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresult'")
    has_singular = result_singular.fetchone() is not None

    result_plural = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresults'")
    has_plural = result_plural.fetchone() is not None

    if has_plural and has_singular:
        # Both types coexist (normal migration path):
        #   - "sessionresult" was created by 405aa2c39458 (2019, kernels.result)
        #   - "sessionresults" was created by b6b884fbae1f (2022, sessions.result)
        #   - ffcf0ed13a26 skipped rename because both existed
        # Fix: alter sessions.result to use the singular type, then drop plural.
        conn.exec_driver_sql(
            "ALTER TABLE sessions ALTER COLUMN result"
            " TYPE sessionresult USING result::text::sessionresult"
        )
        conn.exec_driver_sql("DROP TYPE sessionresults")
    elif has_plural and not has_singular:
        # Only plural exists (ffcf0ed13a26 was never applied, or was skipped).
        # Rename to singular to match EnumType(SessionResult) convention.
        conn.exec_driver_sql("ALTER TYPE sessionresults RENAME TO sessionresult")


def downgrade() -> None:
    conn = op.get_bind()

    result_singular = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresult'")
    has_singular = result_singular.fetchone() is not None

    result_plural = conn.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'sessionresults'")
    has_plural = result_plural.fetchone() is not None

    if has_singular and not has_plural:
        # Recreate the plural type and revert sessions.result to use it.
        conn.exec_driver_sql(
            "CREATE TYPE sessionresults AS ENUM ('UNDEFINED', 'SUCCESS', 'FAILURE')"
        )
        conn.exec_driver_sql(
            "ALTER TABLE sessions ALTER COLUMN result"
            " TYPE sessionresults USING result::text::sessionresults"
        )
