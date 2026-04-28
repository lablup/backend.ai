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

Revision ID: dec0deba5893
Revises: d1c0f1e2b3a4
Create Date: 2026-04-29

"""

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


def _column_type_name(conn: Connection, table: str, column: str) -> str | None:
    row = conn.execute(
        text(
            "SELECT udt_name FROM information_schema.columns"
            " WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row[0] if row is not None else None


def _drop_column_default(conn: Connection, table: str, column: str) -> None:
    try:
        conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT")
    except Exception as e:
        log.warning("Skipping DROP DEFAULT on %s.%s: %s", table, column, e)


def _alter_column_to_varchar(conn: Connection, table: str, column: str) -> None:
    try:
        conn.exec_driver_sql(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(64) USING {column}::text"
        )
    except Exception as e:
        log.warning("Skipping TYPE conversion of %s.%s to VARCHAR: %s", table, column, e)


def _set_column_default_undefined(conn: Connection, table: str, column: str) -> None:
    try:
        conn.exec_driver_sql(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT 'UNDEFINED'")
    except Exception as e:
        log.warning("Skipping SET DEFAULT on %s.%s: %s", table, column, e)


def _drop_enum_type(conn: Connection, type_name: str) -> None:
    try:
        conn.exec_driver_sql(f"DROP TYPE IF EXISTS {type_name}")
    except Exception as e:
        log.warning("Skipping DROP TYPE %s: %s", type_name, e)


def _create_sessionresult_type_if_missing(conn: Connection) -> None:
    try:
        conn.exec_driver_sql(
            "DO $$ BEGIN"
            " IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionresult') THEN"
            "   CREATE TYPE sessionresult AS ENUM ('UNDEFINED', 'SUCCESS', 'FAILURE');"
            " END IF;"
            " END $$;"
        )
    except Exception as e:
        log.warning("Skipping CREATE TYPE sessionresult: %s", e)


def _alter_column_to_sessionresult(conn: Connection, table: str, column: str) -> None:
    try:
        conn.exec_driver_sql(
            f"ALTER TABLE {table} ALTER COLUMN {column}"
            f" TYPE sessionresult USING {column}::text::sessionresult"
        )
    except Exception as e:
        log.warning("Skipping TYPE conversion of %s.%s to sessionresult: %s", table, column, e)


def _set_column_default_undefined_sessionresult(conn: Connection, table: str, column: str) -> None:
    try:
        conn.exec_driver_sql(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT 'UNDEFINED'::sessionresult"
        )
    except Exception as e:
        log.warning("Skipping SET DEFAULT on %s.%s: %s", table, column, e)


def _convert_to_varchar(conn: Connection, table: str, column: str) -> None:
    type_name = _column_type_name(conn, table, column)
    if type_name is None:
        log.warning("Skipping conversion of %s.%s: column not found", table, column)
        return
    if type_name in ("varchar", "text", "bpchar"):
        return
    _drop_column_default(conn, table, column)
    _alter_column_to_varchar(conn, table, column)
    _set_column_default_undefined(conn, table, column)


def _convert_to_sessionresult(conn: Connection, table: str, column: str) -> None:
    type_name = _column_type_name(conn, table, column)
    if type_name is None:
        log.warning("Skipping revert of %s.%s: column not found", table, column)
        return
    if type_name == "sessionresult":
        return
    _drop_column_default(conn, table, column)
    _alter_column_to_sessionresult(conn, table, column)
    _set_column_default_undefined_sessionresult(conn, table, column)


def upgrade() -> None:
    conn = op.get_bind()

    _convert_to_varchar(conn, "kernels", "result")
    _convert_to_varchar(conn, "sessions", "result")

    for type_name in ("sessionresult", "sessionresults"):
        _drop_enum_type(conn, type_name)


def downgrade() -> None:
    conn = op.get_bind()

    _create_sessionresult_type_if_missing(conn)
    for table in ("kernels", "sessions"):
        _convert_to_sessionresult(conn, table, "result")
