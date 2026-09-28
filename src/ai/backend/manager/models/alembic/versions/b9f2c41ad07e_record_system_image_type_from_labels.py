"""Record the system image type from labels and hold the type column as a string

Backfill `images.type` the way the scan now writes it: system where the image carries
the SYSTEM role label or the `operation` feature, compute otherwise. The role label's
INFERENCE falls to compute, and a row left at the deprecated service value is normalized
to compute so that removing the value later touches no data.

The column becomes a VARCHAR holding the enum's values, so what it stores is lowercase
from here on, where the dropped Postgres enum stored the member names.

Revision ID: b9f2c41ad07e
Revises: d17b4e9c25a8
Create Date: 2026-09-25

"""

from __future__ import annotations

from typing import Final, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "b9f2c41ad07e"  # Part of: NEXT_RELEASE_VERSION
down_revision = "d17b4e9c25a8"
branch_labels = None
depends_on = None

# The enum type the column is dropping. A database built from the models carries the
# name SQLAlchemy derives; one built by replaying the chain carries the name
# 015d84d5a5ef gave.
_ENUM_NAMES: Final[frozenset[str]] = frozenset({"imagetype", "image_type"})
_DOWNGRADE_ENUM_NAME: Final[str] = "imagetype"
_COLUMN_LENGTH: Final[int] = 64

# The labels the dropped enum held, for the downgrade to put back.
_ENUM_LABELS: Final[tuple[str, ...]] = ("COMPUTE", "SYSTEM", "SERVICE")

_COLUMN_TYPE: Final[str] = """
    SELECT t.typname
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_type t ON t.oid = a.atttypid
    WHERE c.relname = 'images' AND a.attname = 'type' AND NOT a.attisdropped
"""

# Both statements key on the labels rather than on what this revision wrote, so a run
# that stopped part way can be repeated.
_ABSORB_SERVICE: Final[str] = "UPDATE images SET type = 'compute' WHERE type = 'service'"

_BACKFILL_SYSTEM: Final[str] = """
    UPDATE images
    SET type = 'system'
    WHERE type <> 'system'
      AND (
        labels ->> 'ai.backend.role' = 'SYSTEM'
        OR 'operation' = ANY (
            string_to_array(coalesce(labels ->> 'ai.backend.features', ''), ' ')
        )
      )
"""


def _column_type(conn: Connection) -> str | None:
    return cast(str | None, conn.scalar(sa.text(_COLUMN_TYPE)))


def backfill(conn: Connection) -> None:
    """Set the type column from the role and feature labels, the way the scan now writes it."""
    conn.execute(sa.text(_ABSORB_SERVICE))
    conn.execute(sa.text(_BACKFILL_SYSTEM))


def upgrade() -> None:
    conn = op.get_bind()
    enum_name = _column_type(conn)
    if enum_name in _ENUM_NAMES:
        # The enum stored the member names, so the values it carried are lowercased here.
        conn.execute(
            sa.text(
                f"ALTER TABLE images ALTER COLUMN type TYPE VARCHAR({_COLUMN_LENGTH})"
                " USING lower(type::text)"
            )
        )
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
    backfill(conn)


def downgrade() -> None:
    """Put the enum back under the name the models derive, whichever name it had before.

    The rows the service type once held are not recoverable.
    """
    conn = op.get_bind()
    if _column_type(conn) in _ENUM_NAMES:
        return
    rendered = ", ".join(f"'{label}'" for label in _ENUM_LABELS)
    conn.execute(sa.text(f"CREATE TYPE {_DOWNGRADE_ENUM_NAME} AS ENUM ({rendered})"))
    conn.execute(
        sa.text(
            f"ALTER TABLE images ALTER COLUMN type TYPE {_DOWNGRADE_ENUM_NAME}"
            f" USING upper(type)::{_DOWNGRADE_ENUM_NAME}"
        )
    )
