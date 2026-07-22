"""drop sessionresult/sessionresults native enum types in favor of VARCHAR

Convert ``kernels.result`` and ``sessions.result`` from PostgreSQL native enum
types (``sessionresult`` / ``sessionresults``) to ``VARCHAR(64)`` and drop the
two enum types entirely. Application code uses ``StrEnumType(SessionResult)``
on top of VARCHAR so the Python enum interface is unchanged; stored values
remain identical (uppercase enum names: ``UNDEFINED``, ``SUCCESS``, ``FAILURE``).

This migration is written to be idempotent across the diverged enum-type
states observed in the wild: the singular ``sessionresult`` may exist, the
plural ``sessionresults`` may exist, both may coexist, or neither may exist
(e.g. an environment that previously failed mid-migration).

Idempotency is achieved with existence/type pre-checks (``information_schema``,
``pg_type``, ``pg_attribute``) so that each DDL statement only runs when it is
actually needed and is not expected to raise. The migration deliberately does
NOT wrap individual statements in ``SAVEPOINT`` blocks: under the asyncpg
driver, every DDL statement invalidates the driver's schema cache, and emitting
a ``SAVEPOINT`` immediately after such a schema-invalidating DDL can leave the
driver without an active transaction block, raising
``NoActiveSQLTransactionError`` on the first upgrade attempt.

Revision ID: dec0deba5893
Revises: d1c0f1e2b3a4
Create Date: 2026-04-29

"""

# Part of: 26.5.0

import logging

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "dec0deba5893"
down_revision = "d1c0f1e2b3a4"
branch_labels = None
depends_on = None

log = logging.getLogger(__name__)

# ``udt_name`` values that indicate the column is already a plain string type
# and therefore needs no enum -> VARCHAR conversion.
_VARCHAR_UDT_NAMES = frozenset(["varchar", "text", "bpchar"])


def _column_udt_name(conn: Connection, table: str, column: str) -> str | None:
    row = conn.execute(
        text(
            "SELECT udt_name FROM information_schema.columns"
            " WHERE table_name = :table AND column_name = :column"
            " AND table_schema = current_schema()"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row[0] if row is not None else None


def _type_exists(conn: Connection, type_name: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM pg_type WHERE typname = :type_name"),
        {"type_name": type_name},
    ).fetchone()
    return row is not None


def _type_has_column_dependents(conn: Connection, type_name: str) -> bool:
    """Return True if any live table column is still typed as ``type_name``.

    Such a column blocks ``DROP TYPE`` (without CASCADE), so the drop is skipped
    when this returns True.
    """
    row = conn.execute(
        text(
            "SELECT 1 FROM pg_attribute a"
            " JOIN pg_type t ON a.atttypid = t.oid"
            " WHERE t.typname = :type_name AND a.attnum > 0 AND NOT a.attisdropped"
            " LIMIT 1"
        ),
        {"type_name": type_name},
    ).fetchone()
    return row is not None


def _convert_column_to_varchar(conn: Connection, table: str, column: str) -> None:
    udt_name = _column_udt_name(conn, table, column)
    if udt_name is None:
        log.warning("Skipping conversion of %s.%s: column not found", table, column)
        return
    if udt_name not in _VARCHAR_UDT_NAMES:
        # Column still uses the native enum type; convert it to VARCHAR.
        # DROP DEFAULT is a no-op (never raises) when no default is set.
        conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT")
        conn.exec_driver_sql(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(64) USING {column}::text"
        )
    # Repair the default unconditionally so it does not still reference the
    # (possibly stale) sessionresult enum type, which would otherwise block
    # DROP TYPE later in this migration on partially-migrated environments.
    conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT 'UNDEFINED'")


def _revert_column_to_sessionresult(conn: Connection, table: str, column: str) -> None:
    udt_name = _column_udt_name(conn, table, column)
    if udt_name is None:
        log.warning("Skipping revert of %s.%s: column not found", table, column)
        return
    if udt_name == "sessionresult":
        return
    conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT")
    conn.exec_driver_sql(
        f"ALTER TABLE {table} ALTER COLUMN {column}"
        f" TYPE sessionresult USING {column}::text::sessionresult"
    )
    conn.exec_driver_sql(
        f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT 'UNDEFINED'::sessionresult"
    )


def _drop_enum_type_if_unused(conn: Connection, type_name: str) -> None:
    if not _type_exists(conn, type_name):
        return
    if _type_has_column_dependents(conn, type_name):
        log.warning("Skipping DROP TYPE %s: columns still depend on it", type_name)
        return
    conn.exec_driver_sql(f"DROP TYPE IF EXISTS {type_name}")


def _create_sessionresult_type_if_missing(conn: Connection) -> None:
    conn.exec_driver_sql(
        "DO $$ BEGIN"
        " IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionresult') THEN"
        "   CREATE TYPE sessionresult AS ENUM ('UNDEFINED', 'SUCCESS', 'FAILURE');"
        " END IF;"
        " END $$;"
    )


def upgrade() -> None:
    conn = op.get_bind()

    _convert_column_to_varchar(conn, "kernels", "result")
    _convert_column_to_varchar(conn, "sessions", "result")

    for type_name in ("sessionresult", "sessionresults"):
        _drop_enum_type_if_unused(conn, type_name)


def downgrade() -> None:
    conn = op.get_bind()

    _create_sessionresult_type_if_missing(conn)
    for table in ("kernels", "sessions"):
        _revert_column_to_sessionresult(conn, table, "result")
