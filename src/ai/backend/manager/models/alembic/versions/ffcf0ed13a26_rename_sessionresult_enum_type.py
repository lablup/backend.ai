"""rename sessionresults enum type to sessionresult

Revision ID: ffcf0ed13a26
Revises: 03ff6767b2e4
Create Date: 2026-02-25 00:00:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ffcf0ed13a26"
down_revision = "03ff6767b2e4"
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


def upgrade() -> None:
    # Unify the enum type name to "sessionresult" (singular)
    # Some databases have "sessionresults" (plural) from 2022 migration (b6b884fbae1f)
    # This migration renames plural to singular to match database convention
    conn = op.get_bind()

    try:
        with conn.begin_nested():
            # Check if both types exist (edge case: database has both enum types)
            result_singular = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresult'"
            )
            has_singular = result_singular.fetchone() is not None

            result_plural = conn.exec_driver_sql(
                "SELECT 1 FROM pg_type WHERE typname = 'sessionresults'"
            )
            has_plural = result_plural.fetchone() is not None

            if has_plural and not has_singular:
                # Normal case: plural exists, rename it to singular
                conn.exec_driver_sql("ALTER TYPE sessionresults RENAME TO sessionresult")
            # If both exist, skip rename to avoid conflict
            # If only singular exists, no action needed
    except sa.exc.DBAPIError as e:
        if not _is_expected_divergence(e):
            raise
        log.warning(
            "Skipping rename of sessionresults -> sessionresult enum type (sqlstate=%s): %s",
            _sqlstate_of(e),
            e,
        )


def downgrade() -> None:
    # Revert to plural form
    # Only attempt if singular form exists and plural does not
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
                # Normal case: singular exists, rename it to plural
                conn.exec_driver_sql("ALTER TYPE sessionresult RENAME TO sessionresults")
            # If both exist, skip rename to avoid conflict
            # If only plural exists, no action needed
    except sa.exc.DBAPIError as e:
        if not _is_expected_divergence(e):
            raise
        log.warning(
            "Skipping rename of sessionresult -> sessionresults enum type (sqlstate=%s): %s",
            _sqlstate_of(e),
            e,
        )
