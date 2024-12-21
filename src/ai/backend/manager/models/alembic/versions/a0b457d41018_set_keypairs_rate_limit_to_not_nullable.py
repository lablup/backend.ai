"""set_keypairs_rate_limit_to_not_nullable

Revision ID: a0b457d41018
Revises: dddf9be580f5
Create Date: 2024-04-17 21:57:17.894468

"""

import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

try:
    from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT

    default_rate_limit = DEFAULT_KEYPAIR_RATE_LIMIT
except ImportError:
    default_rate_limit = 10000


# revision identifiers, used by Alembic.
revision = "a0b457d41018"
down_revision = "dddf9be580f5"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    sync_stmt = textwrap.dedent(
        f"""
        UPDATE keypairs
        SET rate_limit = {default_rate_limit}
        WHERE rate_limit is NULL;
        """
    )
    conn.execute(text(sync_stmt))
    op.alter_column("keypairs", "rate_limit", existing_type=sa.INTEGER(), nullable=False)


def downgrade():
    op.alter_column("keypairs", "rate_limit", existing_type=sa.INTEGER(), nullable=True)
