"""Define a new SessionType: INFERENCE.

Revision ID: 6191962d488a
Revises: b5be363ab05c
Create Date: 2023-02-15 17:35:22.035109

"""
import textwrap

from alembic import op
from sqlalchemy.sql import text

from ai.backend.common.types import SessionTypes

# revision identifiers, used by Alembic.
revision = "6191962d488a"
down_revision = "b5be363ab05c"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TYPE {} ADD VALUE 'INFERENCE';".format(SessionTypes.__name__.lower())))
    conn.execute(
        text(
            "ALTER TABLE sessions ALTER COLUMN session_type TYPE {} USING session_type::text::session_type;".format(
                SessionTypes.__name__.lower()
            )
        )
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            textwrap.dedent(
                """\
            ALTER TABLE sessions
                ALTER COLUMN session_type DROP 'INFERENCE';
            """
            )
        )
    )
