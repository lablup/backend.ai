"""add is_main to keypairs

Which keypair is a user's main one is recorded on ``users.main_access_key``,
whose foreign key is ``ON DELETE SET NULL`` — deleting any keypair silently
clears it. The fact describes a keypair, so it moves onto ``keypairs``, where
deleting the row takes the fact with it.

Backfills only keypairs that their own user points at; a ``main_access_key``
naming another user's keypair is dropped rather than carried over.

Revision ID: a2f6b90c41d7
Revises: c1a7d3f05e28
Create Date: 2026-08-05 15:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a2f6b90c41d7"
down_revision = "c1a7d3f05e28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "keypairs",
        sa.Column("is_main", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.get_bind().execute(
        sa.text("""
            UPDATE keypairs
            SET is_main = true
            FROM users
            WHERE users.main_access_key = keypairs.access_key
              AND users.uuid = keypairs."user"
        """)
    )
    op.create_index(
        "uq_keypairs_is_main",
        "keypairs",
        ["user"],
        unique=True,
        postgresql_where=sa.text("is_main"),
    )


def downgrade() -> None:
    op.drop_index("uq_keypairs_is_main", table_name="keypairs")
    op.drop_column("keypairs", "is_main")
