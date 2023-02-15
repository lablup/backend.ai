"""Define a new SessionType: INFERENCE.

Revision ID: b5be363ab05c
Revises: cace152eefac
Create Date: 2023-02-15 15:24:29.112938

"""
import textwrap

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "b5be363ab05c"
down_revision = "cace152eefac"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            textwrap.dedent(
                """\
            ALTER TABLE sessions
                ALTER COLUMN session_type ADD VALUE 'INFERENCE'
            """
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
                ALTER COLUMN session_type DROP INFERENCE
            """
            )
        )
    )
