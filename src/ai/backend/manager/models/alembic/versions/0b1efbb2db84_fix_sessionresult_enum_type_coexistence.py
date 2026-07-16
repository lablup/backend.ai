"""fix sessionresult enum type when both singular and plural coexist

Revision ID: 0b1efbb2db84
Revises: 7h4m7ygnaao1
Create Date: 2026-03-05 00:00:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0b1efbb2db84"
down_revision = "7h4m7ygnaao1"
branch_labels = None
depends_on = None

log = logging.getLogger(__name__)

# PostgreSQL SQLSTATE codes accepted as "expected divergence" when guarding
# sessionresult-related DDL with try/except. Anything else is reraised.
_EXPECTED_DIVERGENCE_SQLSTATES = frozenset([
    "42710",  # duplicate_object
    "42704",  # undefined_object
    "42P07",  # duplicate_table (index)
    "42P01",  # undefined_table
    "42701",  # duplicate_column
    "42703",  # undefined_column
    "2BP01",  # dependent_objects_still_exist
])


def _sqlstate_of(exc: BaseException) -> str:
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or "?"


def _is_expected_divergence(exc: BaseException) -> bool:
    return _sqlstate_of(exc) in _EXPECTED_DIVERGENCE_SQLSTATES


def _retype_result_column(conn: sa.engine.Connection, table: str, target_type: str) -> None:
    """Change ``<table>.result`` to ``target_type``, carrying its default across.

    PostgreSQL cannot cast an existing column default between two unrelated enum
    types, so ALTER COLUMN ... TYPE fails outright while a default is attached.
    Drop it, retype, then put it back -- the same order dec0deba5893 uses.
    """
    conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN result DROP DEFAULT")
    conn.exec_driver_sql(
        f"ALTER TABLE {table} ALTER COLUMN result"
        f" TYPE {target_type} USING result::text::{target_type}"
    )
    conn.exec_driver_sql(
        f"ALTER TABLE {table} ALTER COLUMN result SET DEFAULT 'UNDEFINED'::{target_type}"
    )


def upgrade() -> None:
    conn = op.get_bind()

    try:
        with conn.begin_nested():
            result_singular = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresult'"
            )
            has_singular = result_singular.fetchone() is not None

            result_plural = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresults'"
            )
            has_plural = result_plural.fetchone() is not None

            if has_plural and has_singular:
                # Both types coexist (normal migration path):
                #   - "sessionresult" was created by 405aa2c39458 (2019, kernels.result)
                #   - "sessionresults" was created by b6b884fbae1f (2022, sessions.result)
                #   - ffcf0ed13a26 skipped rename because both existed
                # Fix: alter sessions.result to use the singular type, then drop plural.
                _retype_result_column(conn, "sessions", "sessionresult")
                conn.exec_driver_sql("DROP TYPE sessionresults")
            elif has_plural and not has_singular:
                # Only plural exists (ffcf0ed13a26 was never applied, or was skipped).
                # Rename to singular to match the StrEnumType(SessionResult, use_name=True)
                # mapping convention for this column.
                conn.exec_driver_sql("ALTER TYPE sessionresults RENAME TO sessionresult")
    except sa.exc.DBAPIError as e:
        if not _is_expected_divergence(e):
            raise
        log.warning(
            "Skipping sessionresult/sessionresults coexistence fix (sqlstate=%s): %s",
            _sqlstate_of(e),
            e,
        )


def downgrade() -> None:
    conn = op.get_bind()

    try:
        with conn.begin_nested():
            result_singular = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresult'"
            )
            has_singular = result_singular.fetchone() is not None

            result_plural = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresults'"
            )
            has_plural = result_plural.fetchone() is not None

            if has_singular and not has_plural:
                # Recreate the plural type and revert sessions.result to use it.
                conn.exec_driver_sql(
                    "CREATE TYPE sessionresults AS ENUM ('UNDEFINED', 'SUCCESS', 'FAILURE')"
                )
                _retype_result_column(conn, "sessions", "sessionresults")
    except sa.exc.DBAPIError as e:
        if not _is_expected_divergence(e):
            raise
        log.warning(
            "Skipping sessionresult/sessionresults coexistence revert (sqlstate=%s): %s",
            _sqlstate_of(e),
            e,
        )
