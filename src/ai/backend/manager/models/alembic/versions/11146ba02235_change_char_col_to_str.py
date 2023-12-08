"""change char col to str

Revision ID: 11146ba02235
Revises: 0f7a4b643940
Create Date: 2022-03-25 12:32:05.637628

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "11146ba02235"
down_revision = "0f7a4b643940"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    op.alter_column("agents", column_name="architecture", type_=sa.String(length=32))
    query = """
    UPDATE agents
    SET architecture = TRIM (architecture);
    """
    conn.execute(text(query))


def downgrade():
    op.alter_column("agents", column_name="architecture", type_=sa.CHAR(length=32))
