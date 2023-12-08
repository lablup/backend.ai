"""add a new session type INFERENCE

Revision ID: b5be363ab05c
Revises: b6b884fbae1f
Create Date: 2023-02-15 15:24:29.112938

Reference: https://www.postgresql.org/message-id/CANu8FiwwBxZZGX23=Na_7bc4DZ-yzd_poKhaoPmN3+SHG08MAg@mail.gmail.com

"""

import textwrap

from alembic import op
from sqlalchemy.sql import text

from ai.backend.common.types import SessionTypes

# revision identifiers, used by Alembic.
revision = "b5be363ab05c"
down_revision = "b6b884fbae1f"
branch_labels = None
depends_on = None

# select enum_range(null::sessiontypes);
typename = SessionTypes.__name__.lower()


def upgrade():
    op.execute(text("ALTER TYPE {} ADD VALUE IF NOT EXISTS 'INFERENCE';".format(typename)))
    op.execute(
        text(
            textwrap.dedent(
                """\
                ALTER TABLE sessions ALTER COLUMN session_type TYPE {} USING session_type::text::sessiontypes;
            """.format(typename)
            )
        )
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            "UPDATE sessions SET session_type = 'INTERACTIVE'::{x} WHERE session_type ="
            " 'INFERENCE'::{x};".format(x=typename)
        )
    )

    cursor = conn.execute(
        text(
            textwrap.dedent(
                """\
                SELECT t.typname, e.enumlabel, e.enumsortorder, e.enumtypid
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                WHERE t.typtype = 'e'
                AND e.enumlabel = 'INFERENCE'
                ORDER BY 1, enumsortorder;
            """
            )
        )
    )

    if (row := next(cursor, None)) is None:
        return

    typname, enumlabel, enumsortorder, enumtypid = row

    conn.execute(
        text(
            textwrap.dedent(
                """\
                DELETE FROM pg_enum
                WHERE enumtypid = {enumtypid}
                AND enumlabel = 'INFERENCE';
            """.format(enumtypid=enumtypid)
            )
        )
    )
